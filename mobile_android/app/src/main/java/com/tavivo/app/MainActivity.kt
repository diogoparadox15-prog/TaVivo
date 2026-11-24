package com.tavivo.app

import android.annotation.SuppressLint
import android.os.Bundle
import android.webkit.PermissionRequest
import android.webkit.WebChromeClient
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.appcompat.app.AppCompatActivity
import java.io.File
import java.io.FileOutputStream
import java.util.concurrent.Executors

class MainActivity : AppCompatActivity() {
    private lateinit var webView: WebView
    private var localServer: LocalServer? = null

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        localServer = LocalServer(this, 9876).also { it.start() }

        // Extrai automaticamente o modelo GGUF embutido no APK na 1ª execução e carrega a IA local
        Executors.newSingleThreadExecutor().execute {
            val modelDir = File(filesDir, "models")
            modelDir.mkdirs()
            val targetModel = File(modelDir, "tavivo_model.gguf")
            if (!targetModel.exists() || targetModel.length() < 10_000_000L) {
                try {
                    val tmpFile = File(modelDir, "tavivo_model.gguf.tmp")
                    assets.open("models/tavivo_model.gguf").use { input ->
                        FileOutputStream(tmpFile).use { output ->
                            val buf = ByteArray(1024 * 1024)
                            while (true) {
                                val read = input.read(buf)
                                if (read <= 0) break
                                output.write(buf, 0, read)
                            }
                        }
                    }
                    tmpFile.renameTo(targetModel)
                } catch (_e: Exception) {
                }
            }
            if (targetModel.exists() && targetModel.length() > 10_000_000L) {
                LlamaBridge.loadModel(targetModel.absolutePath)
            }
        }

        webView = WebView(this).apply {
            settings.javaScriptEnabled = true
            settings.domStorageEnabled = true
            settings.mediaPlaybackRequiresUserGesture = false
            webViewClient = WebViewClient()
            webChromeClient = object : WebChromeClient() {
                override fun onPermissionRequest(request: PermissionRequest?) {
                    request?.grant(request.resources)
                }
            }
        }
        setContentView(webView)
        webView.postDelayed({ webView.loadUrl("http://127.0.0.1:9876/") }, 350)
    }

    override fun onDestroy() {
        localServer?.stop()
        super.onDestroy()
    }
}
