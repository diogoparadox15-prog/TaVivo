package com.tavivo.app

interface TokenCallback {
    fun onToken(piece: String)
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
    external fun nativeGenerateStream(prompt: String, maxTokens: Int, callback: TokenCallback?): String

    fun loadModel(path: String): Boolean {
        if (!libAvailable) return false
        // 4 threads nos cores de performance oferece melhor latência em CPUs ARM64 big.LITTLE
        val cores = Runtime.getRuntime().availableProcessors()
        val threads = if (cores >= 6) 4 else (cores - 1).coerceAtLeast(2)
        return nativeLoadModel(path, threads)
    }

    fun isLoaded(): Boolean = libAvailable && nativeIsLoaded()

    fun generateStream(prompt: String, maxTokens: Int = 280, onToken: (String) -> Unit): String {
        if (!isLoaded()) return ""
        return nativeGenerateStream(
            prompt,
            maxTokens,
            object : TokenCallback {
                override fun onToken(piece: String) {
                    onToken(piece)
                }
            }
        )
    }
}
