from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments, Trainer, BitsAndBytesConfig, DataCollatorForLanguageModeling
from datasets import load_dataset, Dataset
import os
from tqdm import tqdm
from pathlib import Path
from peft import LoraConfig, TaskType, get_peft_model

OUTPUT_DIR = Path("D:/qwen3-enneai")
quantization_config = BitsAndBytesConfig(load_in_4bit=True)

model_id = "Qwen/Qwen3-0.6B"
tokenizer = AutoTokenizer.from_pretrained(model_id)

# 4-bit loading keeps it under 4GB VRAM

lora_config = LoraConfig(
    task_type=TaskType.CAUSAL_LM, # type of task to train on
    inference_mode=False, # set to False for training
    r=8, # dimension of the smaller matrices
    lora_alpha=32, # scaling factor
    lora_dropout=0.1 # dropout of LoRA layers
)

if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

# 4-bit loading keeps it under 4GB VRAM
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    device_map="auto",
    quantization_config=quantization_config,
    trust_remote_code=True  # Add this for Qwen models
)

model.add_adapter(lora_config, adapter_name='enneai')
# Read all documents and store as individual text examples
texts = []
for dirpath, dirnames, filenames in tqdm(os.walk('nl_docs')):
    for filename in filenames:
        full_file_path = os.path.join(dirpath, filename)
        print(f"Processing file: {full_file_path}")
        try:
            with open(full_file_path, "r", encoding='utf-8') as f:
                content = f.read()
                texts.append(content)
        except Exception as e:
            print(f"Error reading file {full_file_path}: {e}")

# Create dataset directly from the text list
dataset = Dataset.from_dict({"text": texts})

def tokenize_fn(examples):
    # Tokenize without padding - we'll use a data collator for dynamic padding
    tokenized = tokenizer(
        examples["text"], 
        truncation=True, 
        padding=False,
        max_length=512,
        return_overflowing_tokens=False
    )
    
    # For causal LM, labels are the same as input_ids
    tokenized["labels"] = tokenized["input_ids"].copy()
    return tokenized

# Tokenize the dataset
dataset = dataset.map(tokenize_fn, batched=True, remove_columns=["text"])

# Use data collator for dynamic padding
data_collator = DataCollatorForLanguageModeling(
    tokenizer=tokenizer,
    mlm=False,  # We're doing causal LM, not masked LM
    pad_to_multiple_of=8  # For better performance
)

args = TrainingArguments(
    output_dir=str(OUTPUT_DIR.absolute()),
    per_device_train_batch_size=1,
    gradient_accumulation_steps=4,
    learning_rate=5e-5,
    num_train_epochs=1,
    fp16=True,
    gradient_checkpointing=True,
    logging_steps=50,
    save_steps=500,
    remove_unused_columns=False,  # Important: keep all columns needed for loss computation
    dataloader_pin_memory=False,
)

trainer = Trainer(
    model=model, 
    args=args, 
    train_dataset=dataset,
    data_collator=data_collator  # Add the data collator
)

trainer.train()

trainer.save_model(str(OUTPUT_DIR.absolute()))
print(f"Model saved to: {OUTPUT_DIR.absolute()}")