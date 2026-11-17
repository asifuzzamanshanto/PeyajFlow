const candidates = [
  "an onion bulb with visible rot or mold",
  "an onion bulb with green shoots sprouting",
  "an onion bulb with cuts or bruises",
  "an intact onion bulb with dry clean skin",
  "a scene without a clear view of an onion bulb",
];
const results = ["rot", "sprouting", "damage", "clear", "uncertain"];
self.onmessage = async ({ data }) => {
  try {
    const { env, pipeline, RawImage } = await import(
      "https://cdn.jsdelivr.net/npm/@huggingface/transformers@3.8.1"
    );
    env.allowLocalModels = false;
    env.backends.onnx.wasm.numThreads = 1;
    const classify = await pipeline(
      "zero-shot-image-classification",
      "Xenova/clip-vit-base-patch32",
      {
        revision: "6b7c523703ae26e39be4b03774966f8571c7f523",
        dtype: "q8",
        device: "wasm",
      },
    );
    const image = await RawImage.fromBlob(
      new Blob([data], { type: "image/jpeg" }),
    );
    const predictions = await classify(image, candidates, {
      hypothesis_template: "A close-up photograph showing {}.",
    });
    const [top, second] = predictions;
    const result =
      top.score >= 0.58 && top.score - second.score >= 0.16
        ? results[candidates.indexOf(top.label)]
        : "uncertain";
    self.postMessage({ result: result ?? "uncertain" });
  } catch {
    self.postMessage({ error: true });
  }
};
