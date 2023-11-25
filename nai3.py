import io
import os
import uuid
import json
import zipfile
import requests
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

# 常量定义
URL = "https://api.novelai.net/ai/generate-image"
IMAGE_FOLDER = "generated_images"
PREVIEW_SIZE = (100, 100)
CONFIG_FILE = "config.json"
DEFAULT_NEGATIVE_PROMPT = ("nsfw, lowres, {bad}, error, fewer, extra, missing, worst quality, "
                           "jpeg artifacts, bad quality, watermark, unfinished, displeasing, "
                           "chromatic aberration, signature, extra digits, artistic error, "
                           "username, scan, [abstract]")

# 确保图像文件夹存在
os.makedirs(IMAGE_FOLDER, exist_ok=True)

# 读取配置文件（如果存在）
if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)
else:
    config = {
        "Authorization": "",
        "negative_prompt": DEFAULT_NEGATIVE_PROMPT,
        "scale": 8,
        "steps": 28,
        "width": 512,
        "height": 512
    }

def save_config():
    # 保存配置到文件
    config["Authorization"] = auth_var.get()
    config["negative_prompt"] = negative_prompt_text_box.get("1.0", tk.END).strip()
    config["scale"] = scale_slider.get()
    config["steps"] = steps_slider.get()
    config["width"] = width_slider.get()
    config["height"] = height_slider.get()
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

def send_request():
    # 发送请求并处理图像

    input_text = input_text_box.get("1.0", tk.END).strip()
    auth_value = auth_var.get()
    negative_prompt_value = negative_prompt_text_box.get("1.0", tk.END).strip()
    seed_value = seed_text_box.get()
    scale_value = scale_slider.get()
    steps_value = steps_slider.get()
    width_value = width_slider.get()
    height_value = height_slider.get()
    
    headers = {
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        'Authorization': auth_value,
        "Cache-Control": "no-cache",
        'Content-Type': 'application/json',
        "Origin": "https://novelai.net",
        "Pragma": "no-cache",
        "Referer": "https://novelai.net/",
        "Sec-Ch-Ua": "\"Not_A Brand\";v=\"8\", \"Chromium\";v=\"120\", \"Microsoft Edge\";v=\"120\"",
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": "\"Windows\"",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0"
    }
    payload = {
        "input": input_text,
        "model": "nai-diffusion-3",
        "action": "generate",
        "parameters": {
            "width": width_value,
            "height": height_value,
            "scale": scale_value,
            "sampler": sampler_dropdown.get(),
            "steps": steps_value,
            "seed": None if seed_value == '' else int(seed_value),
            "negative_prompt": negative_prompt_value,
            "n_samples": 1,
            "ucPreset": 0,
            "qualityToggle": True,
            "sm": False,
            "sm_dyn": False,
            "dynamic_thresholding": False,
            "controlnet_strength": 1,
            "legacy": False,
            "add_original_image": False,
            "uncond_scale": 1,
            "cfg_rescale": 0,
            "noise_schedule": "native"
        }
    }

    # 发送POST请求
    response = requests.post(URL, json=payload, headers=headers)

    # 保存配置
    save_config()

    if response.status_code == 200:
        # 处理返回的ZIP文件并显示图像
        zip_file = zipfile.ZipFile(io.BytesIO(response.content))
        file_name = zip_file.namelist()[0]
        image_data = zip_file.open(file_name)
        image = Image.open(image_data)

        # 使用uuid生成唯一文件名保存图像
        unique_filename = f"{uuid.uuid4().hex}.png"
        image_path = os.path.join(IMAGE_FOLDER, unique_filename)
        image.save(image_path)

        # 更新主图像显示
        display_image(image_path)

        # 更新图像目录新预览
        update_image_directory(image_path)
    else:
        error_label.config(text=f"获取图像失败，状态码：{response.status_code}")

def display_image(image_path):
    # 显示图像
    image = Image.open(image_path)
    image.thumbnail((main_image_frame.winfo_width(), main_image_frame.winfo_height()), Image.ANTIALIAS)
    photo = ImageTk.PhotoImage(image)

    for widget in main_image_frame.winfo_children():
        widget.destroy()

    image_label = tk.Label(main_image_frame, image=photo)
    image_label.image = photo
    image_label.pack(expand=True)

def update_image_directory(image_path):
    # 更新图像目录
    img = Image.open(image_path)
    img.thumbnail(PREVIEW_SIZE, Image.ANTIALIAS)
    photo = ImageTk.PhotoImage(img)

    # 创建一个按钮，并设置它的图像
    preview_button = tk.Button(image_directory_frame, image=photo, command=lambda: display_image(image_path))
    preview_button.image = photo  # 保存对图像的引用
    preview_button.pack(side='top', pady=2)

def initialize_image_directory():

    for image_file in sorted(os.listdir(IMAGE_FOLDER), key=lambda x: os.path.getmtime(os.path.join(IMAGE_FOLDER, x)), reverse=True)[:10]:
        if image_file.endswith(('png', 'jpg', 'jpeg', 'gif')):
            update_image_directory(os.path.join(IMAGE_FOLDER, image_file))

# 创建主窗口
root = tk.Tk()
root.title("图像生成器")

root.grid_rowconfigure(0, weight=1)
root.grid_columnconfigure(0, weight=2) 
root.grid_columnconfigure(1, weight=4)  
root.grid_columnconfigure(2, weight=1)  

left_panel = tk.Frame(root, padx=10, pady=10)
left_panel.grid(row=0, column=0, sticky='nsew')

main_image_frame = tk.Frame(root, bg='grey')
main_image_frame.grid(row=0, column=1, sticky='nsew')

image_directory_frame = tk.Frame(root, bg='grey', padx=10, pady=10)
image_directory_frame.grid(row=0, column=2, sticky='nsew')

main_image_frame.pack_propagate(False)
main_image_frame.config(width=800, height=600) 

# 在图像显示区添加一个标签，用于展示图像
display_label = tk.Label(main_image_frame, bg='grey')
display_label.pack(fill='both', expand=True)

parameters_frame = tk.Frame(left_panel)
parameters_frame.pack(fill='both', expand=True)

input_label = tk.Label(parameters_frame, text="输入提示 (Input Prompt):")
input_label.pack(fill='x', anchor='w')
input_text_box = tk.Text(parameters_frame, height=4)
input_text_box.pack(fill='x')

negative_prompt_label = tk.Label(parameters_frame, text="负面提示 (Negative Prompt):")
negative_prompt_label.pack(fill='x', anchor='w')
negative_prompt_text_box = tk.Text(parameters_frame, height=4)
negative_prompt_text_box.insert('1.0', config.get("negative_prompt", DEFAULT_NEGATIVE_PROMPT))
negative_prompt_text_box.pack(fill='x')

seed_label = tk.Label(parameters_frame, text="种子值 (Seed):")
seed_label.pack(fill='x', anchor='w')
seed_text_box = tk.Entry(parameters_frame)
seed_text_box.pack(fill='x')

sampler_label = tk.Label(parameters_frame, text="选择采样器 (Choose Sampler):")
sampler_label.pack(fill='x', anchor='w')
sampler_options = ["k_dpmpp_2s_ancestral", "DPM++ 2M", "Euler", "Euler Ancestral", "DPM++ SDE", "DDIM"]
sampler_dropdown = ttk.Combobox(parameters_frame, values=sampler_options, state="readonly")
sampler_dropdown.set(sampler_options[0])  # 默认选项
sampler_dropdown.pack(fill='x')

width_label = tk.Label(parameters_frame, text="图像宽度 (Width):")
width_label.pack(fill='x', anchor='w')
width_slider = tk.Scale(parameters_frame, from_=512, to=1024, orient=tk.HORIZONTAL, resolution=32)
width_slider.set(config.get("width", 512))  # 从配置文件加载
width_slider.pack(fill='x')

height_label = tk.Label(parameters_frame, text="图像高度 (Height):")
height_label.pack(fill='x', anchor='w')
height_slider = tk.Scale(parameters_frame, from_=512, to=1024, orient=tk.HORIZONTAL, resolution=32)
height_slider.set(config.get("height", 512))  # 从配置文件加载
height_slider.pack(fill='x')

scale_label = tk.Label(parameters_frame, text="细节程度 (Scale):")
scale_label.pack(fill='x', anchor='w')
scale_slider = tk.Scale(parameters_frame, from_=0, to=15, orient=tk.HORIZONTAL)
scale_slider.set(config.get("scale", 8))  # 从配置文件加载
scale_slider.pack(fill='x')

steps_label = tk.Label(parameters_frame, text="步骤数量 (Steps):")
steps_label.pack(fill='x', anchor='w')
steps_slider = tk.Scale(parameters_frame, from_=1, to=28, orient=tk.HORIZONTAL)
steps_slider.set(config.get("steps", 28))  # 从配置文件加载
steps_slider.pack(fill='x')

auth_label = tk.Label(parameters_frame, text="授权 (Authorization):")
auth_label.pack(fill='x', anchor='w')
auth_var = tk.StringVar(value=config.get("Authorization", ""))
auth_text_box = tk.Entry(parameters_frame, textvariable=auth_var, show="*")
auth_text_box.pack(fill='x')
def update_auth_display_on_focusin(event=None):

    current_auth = auth_var.get()
    auth_text_box.config(show="")
    auth_text_box.delete(0, tk.END)
    if current_auth:  # 只有当auth_var有值时才显示
        auth_text_box.insert(0, current_auth)

def update_auth_display_on_focusout(event=None):

    current_auth = auth_var.get()
    if current_auth:  # 只有当auth_var有值时才转换为星号
        auth_text_box.config(show="*")
    else:
        auth_text_box.config(show="")

auth_text_box.bind("<FocusIn>", update_auth_display_on_focusin)
auth_text_box.bind("<FocusOut>", update_auth_display_on_focusout)

send_button = tk.Button(parameters_frame, text='生成图像 (Generate Image)', command=send_request)
send_button.pack(fill='x', pady=5)

error_label = tk.Label(parameters_frame, text="", fg="red")
error_label.pack(fill='x')

initialize_image_directory()

display_label = tk.Label(main_image_frame)
display_label.pack(fill='both', expand=True)

def display_image(image_path):
    # 更新主图像显示区域的图像
    image = Image.open(image_path)
    image.thumbnail((main_image_frame.winfo_width(), main_image_frame.winfo_height()), Image.Resampling.LANCZOS)
    photo = ImageTk.PhotoImage(image)

    display_label.config(image=photo)
    display_label.image = photo  # 保留对图像的引用

def initialize_image_directory():
    # 清空预览区域
    for widget in image_directory_frame.winfo_children():
        widget.destroy()

    image_files = sorted(
        [f for f in os.listdir(IMAGE_FOLDER) if f.endswith(('png', 'jpg', 'jpeg', 'gif'))],
        key=lambda x: os.path.getmtime(os.path.join(IMAGE_FOLDER, x)),
        reverse=True
    )
    for image_file in image_files[:6]:
        image_path = os.path.join(IMAGE_FOLDER, image_file)
        update_image_directory(image_path)

root.mainloop()
