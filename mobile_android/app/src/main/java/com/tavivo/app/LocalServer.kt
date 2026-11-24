package com.tavivo.app

import android.content.Context
import org.json.JSONArray
import org.json.JSONObject
import java.io.BufferedReader
import java.io.InputStreamReader
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

    private fun handleClient(socket: Socket) {
        socket.use { s ->
            val reader = BufferedReader(InputStreamReader(s.getInputStream()))
            val out = s.getOutputStream()
            val requestLine = reader.readLine() ?: return
            val parts = requestLine.split(" ")
            if (parts.size < 2) return
            val method = parts[0]
            val fullPath = parts[1]
            var contentLength = 0
            while (true) {
                val line = reader.readLine() ?: break
                if (line.isEmpty()) break
                if (line.lowercase().startsWith("content-length:")) {
                    contentLength = line.substringAfter(":").trim().toIntOrNull() ?: 0
                }
            }

            val pathOnly = fullPath.substringBefore("?")
            val queryStr = fullPath.substringAfter("?", "")

            if (method == "POST" && pathOnly == "/api/chat") {
                val buf = CharArray(contentLength.coerceAtMost(2 * 1024 * 1024))
                var read = 0
                while (read < buf.size) {
                    val r = reader.read(buf, read, buf.size - read)
                    if (r <= 0) break
                    read += r
                }
                handleChat(out, String(buf, 0, read))
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
        val hits = searchArticles(userMsg, 3)

        val headers = "HTTP/1.1 200 OK\r\n" +
            "Content-Type: text/event-stream; charset=utf-8\r\n" +
            "Cache-Control: no-cache\r\n" +
            "Connection: close\r\n\r\n"
        out.write(headers.toByteArray())
        out.flush()

        fun sendEvent(obj: JSONObject) {
            out.write("data: ${obj}\n\n".toByteArray())
            out.flush()
        }

        val reply = if (LlamaBridge.isLoaded()) {
            val ctx = hits.joinToString("\n\n") { "### ${it.title}\n${it.text.take(1200)}" }
            val prompt = "Você é o TaVivo, I.A. de sobrevivência 100% offline. Responda em português do Brasil de forma objetiva usando o contexto:\n$ctx\n\nPergunta: $userMsg\nResposta:"
            LlamaBridge.generate(prompt, 384).ifBlank { fallbackReply(hits) }
        } else {
            fallbackReply(hits)
        }

        sendEvent(JSONObject().put("type", "token").put("text", reply))
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
