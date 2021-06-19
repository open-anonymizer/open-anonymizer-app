from transformers import AutoModelForTokenClassification, AutoTokenizer

def get_model(model):
    """Load model from Hugginface Model Hub"""
    try:
        model = AutoModelForTokenClassification.from_pretrained(model)
        model.save_pretrained('./models')
    except Exception as e:
        raise(e)
  
def get_tokenizer(tokenizer):
    """Load tokenizer from Hugginface Model Hub"""
    try:
        tokenizer = AutoTokenizer.from_pretrained(tokenizer)
        tokenizer.save_pretrained('./models')
    except Exception as e:
        raise(e)


get_model('xlm-roberta-large-finetuned-conll03-german')
get_tokenizer('xlm-roberta-large-finetuned-conll03-german')
