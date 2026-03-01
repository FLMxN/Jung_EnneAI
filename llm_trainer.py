from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    BitsAndBytesConfig,
    DataCollatorForLanguageModeling
)
from datasets import Dataset
from peft import LoraConfig, TaskType, get_peft_model
from pathlib import Path
from tqdm import tqdm
import torch
import os

# === CONFIG ===
MODEL_ID = "Qwen/Qwen2.5-0.5B"
OUTPUT_DIR = Path("D:/qwen2.5-enneai")

# 4-bit quantization keeps memory low for GTX 1650
quantization_config = BitsAndBytesConfig(load_in_4bit=True)

# === TOKENIZER ===
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

# === MODEL + LoRA ===
model = AutoModelForCausalLM.from_pretrained(
    MODEL_ID,
    device_map="auto",
    quantization_config=quantization_config,
    dtype=torch.float16,
    trust_remote_code=True
)

lora_config = LoraConfig(
    task_type=TaskType.CAUSAL_LM,
    inference_mode=False,
    r=8,
    lora_alpha=32,
    lora_dropout=0.1
)

model = get_peft_model(model, lora_config)
print("✅ Model + LoRA loaded successfully.")

texts = []
base_dir = "nl_docs"
for dirpath, _, filenames in os.walk(base_dir):
    for filename in tqdm(filenames, desc="Loading documents"):
        file_path = os.path.join(dirpath, filename)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if len(content) > 0:
                    texts.append(content)
        except Exception as e:
            print(f"⚠️ Error reading {file_path}: {e}")

print(f"Loaded {len(texts)} documents.")

dataset = Dataset.from_dict({"text": texts})

def tokenize_fn(examples):
    result = tokenizer(
        examples["text"],
        truncation=True,
        padding=False,
        max_length=512,
        return_overflowing_tokens=False
    )
    result["labels"] = result["input_ids"].copy()
    return result

dataset = dataset.map(tokenize_fn, batched=True, remove_columns=["text"])

# === COLLATOR ===
data_collator = DataCollatorForLanguageModeling(
    tokenizer=tokenizer,
    mlm=False,
    pad_to_multiple_of=8
)

# === TRAINING ARGS ===
training_args = TrainingArguments(
    output_dir=str(OUTPUT_DIR),
    num_train_epochs=30,                    
    per_device_train_batch_size=1,
    # gradient_accumulation_steps=4,
    learning_rate=1e-5,                      
    lr_scheduler_type="cosine",
    warmup_ratio=0.05,
    fp16=True,
    # gradient_checkpointing=True,
    logging_steps=20,
    save_steps=500,
    save_total_limit=2,
    dataloader_pin_memory=False,
    remove_unused_columns=False,
    report_to="none"                        
)

# === TRAINER ===
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=dataset,
    data_collator=data_collator
)

print("🚀 Starting training...")
trainer.train()

trainer.save_model(str(OUTPUT_DIR))
print(f"✅ Model saved to {OUTPUT_DIR.resolve()}")
