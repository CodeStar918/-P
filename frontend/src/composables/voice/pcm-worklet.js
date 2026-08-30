// PCM 采集 AudioWorklet 处理器：替代已废弃的 ScriptProcessor。
// 每帧把 Float32 采样拷贝后经 port 推给主线程（handleAudioChunk 统一处理）。
class PcmCaptureProcessor extends AudioWorkletProcessor {
  process(inputs) {
    const input = inputs[0]
    if (input && input[0]) {
      this.port.postMessage(input[0].slice(0))
    }
    return true
  }
}

registerProcessor('pcm-capture', PcmCaptureProcessor)
