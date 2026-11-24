package com.tavivo.app

interface TokenCallback {
    fun onTokenBytes(bytes: ByteArray)
}

object LlamaBridge {
    private var libAvailable = false

    init {
        try {
            System.loadLibrary("tavivo_llama")
            libAvailable = true
        } catch (_e: UnsatisfiedLinkError) {
            libAvailable = false
        }
    }

    external fun nativeLoadModel(path: String, nThreads: Int): Boolean
    external fun nativeIsLoaded(): Boolean
    external fun nativeGenerateStream(promptBytes: ByteArray, maxTokens: Int, callback: TokenCallback?): Boolean

    fun loadModel(path: String): Boolean {
        if (!libAvailable) return false
        val cores = Runtime.getRuntime().availableProcessors()
        val threads = if (cores >= 6) 4 else (cores - 1).coerceAtLeast(2)
        return nativeLoadModel(path, threads)
    }

    fun isLoaded(): Boolean = libAvailable && nativeIsLoaded()

    fun generateStream(prompt: String, maxTokens: Int = 260, onToken: (String) -> Unit): Boolean {
        if (!isLoaded()) return false
        return nativeGenerateStream(
            prompt.toByteArray(Charsets.UTF_8),
            maxTokens,
            object : TokenCallback {
                override fun onTokenBytes(bytes: ByteArray) {
                    val text = String(bytes, Charsets.UTF_8)
                    if (text.isNotEmpty()) onToken(text)
                }
            }
        )
    }
}
