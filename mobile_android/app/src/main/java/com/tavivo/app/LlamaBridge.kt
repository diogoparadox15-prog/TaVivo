package com.tavivo.app

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
    external fun nativeGenerate(prompt: String, maxTokens: Int): String

    fun loadModel(path: String): Boolean {
        if (!libAvailable) return false
        val threads = (Runtime.getRuntime().availableProcessors() - 1).coerceIn(2, 6)
        return nativeLoadModel(path, threads)
    }

    fun isLoaded(): Boolean = libAvailable && nativeIsLoaded()

    fun generate(prompt: String, maxTokens: Int = 384): String {
        if (!isLoaded()) return ""
        return nativeGenerate(prompt, maxTokens)
    }
}
