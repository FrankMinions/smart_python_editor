import os
import json
import torch
import argparse
from flask import Flask, jsonify, request
from flask_cors import cross_origin
from transformers import LlamaTokenizer, LlamaForCausalLM

parser = argparse.ArgumentParser()
parser.add_argument('--model_name_or_path', default='frankminors123/Chinese-CodeLlama-7B-SFT-V2', type=str)
parser.add_argument('--gpus', default="0, 1, 2, 3", type=str)
parser.add_argument('--only_cpu', default=False, help='only use CPU for inference')
args = parser.parse_args()

app = Flask(__name__)

if args.only_cpu is True:
    args.gpus = ""
os.environ["CUDA_VISIBLE_DEVICES"] = args.gpus

if torch.cuda.is_available():
    device = torch.device(0)
else:
    device = torch.device('cpu')


class Template:
    def __init__(self):
        self.template = (
            "下面是描述一项任务的指令，并且与一则输入配对用来提供更多的上下文。请给出尽可能满足请求的回答.\n"
            "### 指令:\n{instruction}\n### 输入:\n{input}\n### 回答:\n"
        )
        self.response_split = "### 回答:"


def get_request_data(req: request):
    data = json.loads(req.data)
    return data["prompt"], data["input"]


tokenizer = LlamaTokenizer.from_pretrained(pretrained_model_name_or_path=args.model_name_or_path, trust_remote_code=True)
model = LlamaForCausalLM.from_pretrained(pretrained_model_name_or_path=args.model_name_or_path, trust_remote_code=True, device_map="auto")

template = Template()
prompt_template = template.template
response_split = template.response_split

generation_config = dict(
    temperature=0.5,
    top_k=0,
    top_p=0.8,
    do_sample=True,
    repetition_penalty=1.05,
    max_new_tokens=1024
)


@app.route('/codeLlama', methods=["POST"])
@cross_origin()
def chat():
    prompt_tokens, completion_tokens = 0, 0
    response = None
    try:
        prompt, inputs = get_request_data(request)
        input_text = prompt_template.format_map({'instruction': prompt, 'input': inputs})
        with torch.no_grad():
            tokenized_data = tokenizer(input_text, return_tensors="pt", add_special_tokens=False)
            prompt_tokens = len(tokenizer.tokenize(input_text))
            generation_output = model.generate(
                input_ids=tokenized_data["input_ids"].to(device),
                eos_token_id=tokenizer.eos_token_id,
                **generation_config
            )
            s = generation_output[0]
            response = tokenizer.decode(s, skip_special_tokens=True).split(response_split)[1].strip()
            completion_tokens = len(tokenizer.tokenize(response))
            return jsonify({'success': True,
                            'code': 200,
                            'message': 'success',
                            'data': {'response': response,
                                     'usage': {'prompt_tokens': prompt_tokens,
                                               'completion_tokens': completion_tokens,
                                               'total_tokens': prompt_tokens + completion_tokens}}})

    except Exception as e:
        return jsonify({'success': False,
                        'code': 500,
                        'message': str(e),
                        'data': {'response': response,
                                 'usage': {'prompt_tokens': prompt_tokens,
                                           'completion_tokens': completion_tokens,
                                           'total_tokens': prompt_tokens + completion_tokens}}})


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000)
