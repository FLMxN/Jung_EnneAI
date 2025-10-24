from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments, Trainer, BitsAndBytesConfig
from datasets import load_dataset
import os
from tqdm import tqdm
from pathlib import Path

OUTPUT_DIR = Path("D:/qwen3-enneai")
quantization_config = BitsAndBytesConfig(load_in_4bit=True)

model_id = "Qwen/Qwen3-0.6B"
tokenizer = AutoTokenizer.from_pretrained(model_id)

# 4-bit loading keeps it under 4GB VRAM
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    device_map="auto",
    quantization_config=quantization_config
)
docs = []
for dirpath, dirnames, filenames in tqdm(os.walk('nl_docs')):
        for filename in filenames:
            full_file_path = os.path.join(dirpath, filename)
            print(f"Processing file: {full_file_path}")
            with open(full_file_path, "r", encoding='utf-8') as f:
                content = f.read()
                docs.append(str(content))

dataset = load_dataset("text", data_files={"train": docs})

def tokenize_fn(examples):
    return tokenizer(examples["text"], truncation=True)
dataset = dataset.map(tokenize_fn, batched=True, remove_columns=["text"])

args = TrainingArguments(
    output_dir=str(OUTPUT_DIR.absolute()),
    per_device_train_batch_size=1,
    gradient_accumulation_steps=4,
    learning_rate=5e-5,
    num_train_epochs=1,
    fp16=True,
    gradient_checkpointing=True,
    logging_steps=50,
)

trainer = Trainer(model=model, args=args, train_dataset=dataset["train"])
trainer.train()

trainer.save_model(str(OUTPUT_DIR.absolute()))
print(f"Model saved to: {OUTPUT_DIR.absolute()}")