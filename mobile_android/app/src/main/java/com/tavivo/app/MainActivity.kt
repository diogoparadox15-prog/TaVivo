package com.tavivo.app

import android.annotation.SuppressLint
import android.os.Bundle
import android.webkit.PermissionRequest
import android.webkit.WebChromeClient
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.appcompat.app.AppCompatActivity
import java.io.File
import java.util.concurrent.Executors

class MainActivity : AppCompatActivity() {
    private lateinit var webView: WebView
    private var localServer: LocalServer? = null

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        localServer = LocalServer(this, 9876).also { it.start() }

        // Carrega automaticamente o modelo GGUF se estiver na pasta de arquivos do app
        Executors.newSingleThreadExecutor().execute {
            val modelDir = File(getExternalFilesDir(null), "models")
            modelDir.mkdirs()
            val gguf = modelDir.listFiles()?.firstOrNull { it.name.endsWith(".gguf") && !it.name.startsWith("mmproj") }
            if (gguf != null && gguf.exists()) {
                LlamaBridge.loadModel(gguf.absolutePath)
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
