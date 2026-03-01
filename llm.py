from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, set_seed
from pathlib import Path
import torch

# === SETTINGS ===
MODEL_PATH = Path("D:/qwen2.5-enneai")
quantization_config = BitsAndBytesConfig(load_in_4bit=True)
set_seed(42)

# === LOAD TOKENIZER ===
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

# === LOAD MODEL ===
model = AutoModelForCausalLM.from_pretrained(
    MODEL_PATH,
    device_map="auto",
    quantization_config=quantization_config,
    dtype=torch.float16,
)
model.eval()

# === INFERENCE LOOP ===
while True:
    prompt = input("\n🗨️  Input text (or 'exit' to quit): ").strip()
    if not prompt or prompt.lower() in {"exit", "quit"}:
        break

    # Encode prompt
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    # Generate response
    with torch.inference_mode():
        generated_ids = model.generate(
            **inputs,
            max_new_tokens=200,
            temperature=0.4,
            top_p=0.9,
            repetition_penalty=1.1,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id
        )

    # Decode the newly generated part
    output_text = tokenizer.decode(
        generated_ids[0][inputs["input_ids"].shape[1]:],
        skip_special_tokens=True
    )

    print("\n💬 Output:\n", output_text)
