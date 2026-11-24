package com.tavivo.app

import android.content.Context
import org.json.JSONArray
import org.json.JSONObject
import java.io.BufferedInputStream
import java.io.ByteArrayOutputStream
import java.io.InputStream
import java.io.OutputStream
import java.net.InetAddress
import java.net.ServerSocket
import java.net.Socket
import java.net.URLDecoder
import java.text.Normalizer
import java.util.concurrent.Executors

data class OfflineArticle(
    val id: Int,
    val title: String,
    val source: String,
    val topic: String,
    val license: String,
    val text: String,
    val normHaystack: String
)

class LocalServer(private val context: Context, private val port: Int = 9876) {
    private var serverSocket: ServerSocket? = null
    private val pool = Executors.newCachedThreadPool()
    private val articles = mutableListOf<OfflineArticle>()

    fun start() {
        loadOfflineLibrary()
        pool.execute {
            try {
                serverSocket = ServerSocket(port, 32, InetAddress.getByName("127.0.0.1"))
                while (serverSocket?.isClosed == false) {
                    val client = serverSocket!!.accept()
                    pool.execute { handleClient(client) }
                }
            } catch (_e: Exception) {
            }
        }
    }

    fun stop() {
        try {
            serverSocket?.close()
        } catch (_e: Exception) {
        }
        pool.shutdownNow()
    }

    private fun normalize(s: String): String {
        val nfd = Normalizer.normalize(s.lowercase(), Normalizer.Form.NFD)
        return nfd.replace(Regex("[\\p{InCombiningDiacriticalMarks}]"), "")
    }

    private fun loadOfflineLibrary() {
        try {
            val raw = context.assets.open("www/library_offline.json").bufferedReader().use { it.readText() }
            val root = JSONObject(raw)
            val arr = root.optJSONArray("articles") ?: JSONArray()
            articles.clear()
            for (i in 0 until arr.length()) {
                val obj = arr.getJSONObject(i)
                val title = obj.optString("title")
                val text = obj.optString("text")
                articles.add(
                    OfflineArticle(
                        id = obj.optInt("id"),
                        title = title,
                        source = obj.optString("source"),
                        topic = obj.optString("topic"),
                        license = obj.optString("license"),
                        text = text,
                        normHaystack = normalize("$title $text")
                    )
                )
            }
        } catch (_e: Exception) {
        }
    }

    private fun searchArticles(query: String, limit: Int = 8): List<OfflineArticle> {
        val terms = normalize(query).split(Regex("\\s+")).filter { it.length > 1 }
        if (terms.isEmpty()) return emptyList()
        return articles.mapNotNull { art ->
            var score = 0
            val normTitle = normalize(art.title)
            for (t in terms) {
                if (art.normHaystack.contains(t)) {
                    score += if (normTitle.contains(t)) 4 else 1
                }
            }
            if (score > 0) Pair(score, art) else null
        }.sortedByDescending { it.first }.take(limit).map { it.second }
    }

    private fun readHttpLine(input: InputStream): String? {
        val baos = ByteArrayOutputStream()
        var prev = -1
        while (true) {
            val b = input.read()
            if (b == -1) {
                return if (baos.size() == 0) null else baos.toString("UTF-8")
            }
            if (b == '\n'.code) {
                val bytes = baos.toByteArray()
                val len = if (prev == '\r'.code && bytes.isNotEmpty()) bytes.size - 1 else bytes.size
                return String(bytes, 0, len, Charsets.UTF_8)
            }
            baos.write(b)
            prev = b
        }
    }

    private fun readExactBytes(input: InputStream, length: Int): ByteArray {
        val buf = ByteArray(length)
        var read = 0
        while (read < length) {
            val r = input.read(buf, read, length - read)
            if (r <= 0) break
            read += r
        }
        return if (read == length) buf else buf.copyOf(read)
    }

    private fun handleClient(socket: Socket) {
        socket.use { s ->
            s.soTimeout = 15000
            val input = BufferedInputStream(s.getInputStream())
            val out = s.getOutputStream()
            val requestLine = readHttpLine(input) ?: return
            val parts = requestLine.split(" ")
            if (parts.size < 2) return
            val method = parts[0]
            val fullPath = parts[1]
            var contentLength = 0
            while (true) {
                val line = readHttpLine(input) ?: break
                if (line.isEmpty()) break
                if (line.lowercase().startsWith("content-length:")) {
                    contentLength = line.substringAfter(":").trim().toIntOrNull() ?: 0
                }
            }

            val pathOnly = fullPath.substringBefore("?")
            val queryStr = fullPath.substringAfter("?", "")

            if (method == "POST" && pathOnly == "/api/chat") {
                val safeLen = contentLength.coerceIn(0, 4 * 1024 * 1024)
                val bodyBytes = readExactBytes(input, safeLen)
                s.soTimeout = 0
                handleChat(out, String(bodyBytes, Charsets.UTF_8))
                return
            }

            when {
                pathOnly == "/" || pathOnly == "/index.html" -> sendAsset(out, "www/index.html", "text/html; charset=utf-8")
                pathOnly == "/manifest.json" -> sendAsset(out, "www/manifest.json", "application/manifest+json; charset=utf-8")
                pathOnly == "/sw.js" -> sendAsset(out, "www/sw.js", "text/javascript; charset=utf-8")
                pathOnly.startsWith("/static/") -> {
                    val rel = pathOnly.removePrefix("/static/").trimStart('/')
                    sendAsset(out, "www/$rel", mimeType(rel))
                }
                pathOnly == "/api/status" -> {
                    val j = JSONObject()
                        .put("ai_online", LlamaBridge.isLoaded())
                        .put("ai_port", 9931)
                        .put("library_online", articles.isNotEmpty())
                        .put("articles", articles.size)
                        .put("sources", articles.map { it.source }.distinct().size)
                    sendJson(out, 200, j.toString())
                }
                pathOnly == "/api/sources" -> {
                    val grouped = articles.groupBy { it.source }
                    val arr = JSONArray()
                    grouped.forEach { (srcName, list) ->
                        val arts = JSONArray()
                        list.forEach { a -> arts.put(JSONObject().put("title", a.title).put("id", a.id)) }
                        arr.put(
                            JSONObject()
                                .put("label", srcName)
                                .put("topic", list.firstOrNull()?.topic ?: "")
                                .put("license", list.firstOrNull()?.license ?: "")
                                .put("articles", arts)
                        )
                    }
                    sendJson(out, 200, JSONObject().put("sources", arr).toString())
                }
                pathOnly == "/api/legal" -> {
                    val text = try {
                        context.assets.open("www/AVISO_LEGAL.md").bufferedReader().use { it.readText() }
                    } catch (_e: Exception) {
                        "TaVivo Offline Android — Consulte sempre profissionais de saúde quando disponíveis."
                    }
                    sendJson(out, 200, JSONObject().put("text", text).toString())
                }
                pathOnly == "/api/search" -> {
                    val q = parseQueryParam(queryStr, "q")
                    val hits = searchArticles(q, 15)
                    val arr = JSONArray()
                    hits.forEach { a ->
                        arr.put(
                            JSONObject()
                                .put("id", a.id)
                                .put("title", a.title)
                                .put("source", a.source)
                                .put("snippet", a.text.take(280) + "...")
                        )
                    }
                    sendJson(out, 200, JSONObject().put("query", q).put("results", arr).toString())
                }
                pathOnly == "/api/article" -> {
                    val id = parseQueryParam(queryStr, "id").toIntOrNull() ?: -1
                    val art = articles.find { it.id == id }
                    if (art == null) {
                        sendJson(out, 404, "{\"error\":\"Artigo não encontrado\"}")
                    } else {
                        val partsArr = JSONArray().put(JSONObject().put("id", art.id).put("text", art.text))
                        val j = JSONObject()
                            .put("id", art.id)
                            .put("title", art.title)
                            .put("source", art.source)
                            .put("license", art.license)
                            .put("parts", partsArr)
                        sendJson(out, 200, j.toString())
                    }
                }
                else -> sendJson(out, 404, "{\"error\":\"Rota não encontrada\"}")
            }
        }
    }

    private fun handleChat(out: OutputStream, body: String) {
        val req = try { JSONObject(body) } catch (_e: Exception) { JSONObject() }
        val userMsg = req.optString("message", "").trim()
        val hits = searchArticles(userMsg, 2)

        val headers = "HTTP/1.1 200 OK\r\n" +
            "Content-Type: text/event-stream; charset=utf-8\r\n" +
            "Cache-Control: no-cache\r\n" +
            "Connection: close\r\n\r\n"
        out.write(headers.toByteArray())
        out.flush()

        fun sendEvent(obj: JSONObject) {
            try {
                out.write("data: ${obj}\n\n".toByteArray())
                out.flush()
            } catch (_e: Exception) {
            }
        }

        if (LlamaBridge.isLoaded()) {
            val ctx = if (hits.isNotEmpty()) {
                hits.joinToString("\n\n") { "### ${it.title}\n${it.text.take(450)}" }
            } else {
                ""
            }
            val systemPrompt = if (ctx.isNotEmpty()) {
                "Você é o TaVivo, I.A. de sobrevivência 100% offline. " +
                    "Responda SEMPRE em português do Brasil, de forma curta, direta e em tópicos práticos. " +
                    "Em dúvidas médicas e dosagens, siga os manuais abaixo sem inventar doses em mg/ml. " +
                    "Em conhecimento geral, responda normalmente com clareza.\n\n" +
                    "MANUAIS RELEVANTES:\n$ctx"
            } else {
                "Você é o TaVivo, I.A. de sobrevivência 100% offline. " +
                    "Responda SEMPRE em português do Brasil, de forma curta, direta e prática usando seu conhecimento. " +
                    "Nunca recuse perguntas gerais dizendo que não está na biblioteca; apenas não invente dosagens médicas em mg/ml."
            }
            // Pre-fecha <think></think> para o modelo pular o raciocinio longo e responder na hora
            val chatMlPrompt = "<|im_start|>system\n$systemPrompt<|im_end|>\n" +
                "<|im_start|>user\n$userMsg<|im_end|>\n" +
                "<|im_start|>assistant\n<think>\n\n</think>\n"

            var streamedAny = false
            var inThink = false
            LlamaBridge.generateStream(chatMlPrompt, 220) { rawPiece ->
                var piece = rawPiece
                if (piece.contains("<think>")) {
                    inThink = true
                    piece = piece.substringBefore("<think>")
                }
                if (piece.contains("</think>")) {
                    inThink = false
                    piece = piece.substringAfter("</think>")
                }
                if (inThink) return@generateStream
                piece = piece.replace("<think>", "").replace("</think>", "")
                if (piece.isEmpty()) return@generateStream
                if (!streamedAny) {
                    piece = piece.trimStart('\n', '\r')
                    if (piece.isEmpty()) return@generateStream
                }
                streamedAny = true
                sendEvent(JSONObject().put("type", "token").put("text", piece))
            }
            if (!streamedAny) {
                sendEvent(JSONObject().put("type", "token").put("text", fallbackReply(hits)))
            }
        } else {
            sendEvent(JSONObject().put("type", "token").put("text", fallbackReply(hits)))
        }

        if (hits.isNotEmpty()) {
            val srcArr = JSONArray()
            hits.forEach { srcArr.put(JSONObject().put("id", it.id).put("title", it.title).put("source", it.source)) }
            sendEvent(JSONObject().put("type", "sources").put("sources", srcArr))
        }
        sendEvent(JSONObject().put("type", "done"))
    }

    private fun fallbackReply(hits: List<OfflineArticle>): String {
        if (hits.isEmpty()) {
            return "Preparando motor de I.A. offline pela primeira vez... aguarde alguns segundos até o indicador ficar verde (🟢) ou pesquise diretamente na Biblioteca Offline."
        }
        val top = hits.first()
        return "[Motor de I.A. offline inicializando — exibindo manual direto da biblioteca]\n\n📖 ${top.title}\n\n${top.text}"
    }

    private fun parseQueryParam(qs: String, key: String): String {
        for (pair in qs.split("&")) {
            val kv = pair.split("=", limit = 2)
            if (kv.size == 2 && kv[0] == key) {
                return URLDecoder.decode(kv[1], "UTF-8")
            }
        }
        return ""
    }

    private fun mimeType(name: String): String = when {
        name.endsWith(".html") -> "text/html; charset=utf-8"
        name.endsWith(".css") -> "text/css; charset=utf-8"
        name.endsWith(".js") -> "text/javascript; charset=utf-8"
        name.endsWith(".json") -> "application/json; charset=utf-8"
        name.endsWith(".svg") -> "image/svg+xml"
        name.endsWith(".png") -> "image/png"
        else -> "application/octet-stream"
    }

    private fun sendAsset(out: OutputStream, assetPath: String, contentType: String) {
        try {
            val bytes = context.assets.open(assetPath).use { it.readBytes() }
            val hdr = "HTTP/1.1 200 OK\r\nContent-Type: $contentType\r\nContent-Length: ${bytes.size}\r\nCache-Control: no-store\r\n\r\n"
            out.write(hdr.toByteArray())
            out.write(bytes)
            out.flush()
        } catch (_e: Exception) {
            sendJson(out, 404, "{\"error\":\"Asset não encontrado\"}")
        }
    }

    private fun sendJson(out: OutputStream, code: Int, body: String) {
        val bytes = body.toByteArray(Charsets.UTF_8)
        val hdr = "HTTP/1.1 $code OK\r\nContent-Type: application/json; charset=utf-8\r\nContent-Length: ${bytes.size}\r\nCache-Control: no-store\r\n\r\n"
        out.write(hdr.toByteArray())
        out.write(bytes)
        out.flush()
    }
}
