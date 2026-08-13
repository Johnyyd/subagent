import os
import json
import subprocess
import re
import argparse # Thêm thư viện này để bắt tham số CLI

def call_free_claude(prompt):
    # Dùng cách này nếu tool bắt buộc phải gõ prompt vào input sau khi bật tool lên
    process = subprocess.run(
        ["free-claude-code"], 
        input=prompt, 
        capture_output=True, 
        text=True, 
        encoding='utf-8'
    )
    return process.stdout

def generate_plan(project_requirement):
    prompt = f"""
    Bạn là Technical Lead. Hãy chia dự án sau thành các task nhỏ, hoàn toàn độc lập.
    Trả về CHỈ một mảng JSON hợp lệ chứa các object, không giải thích gì thêm, cấu trúc:
    [
        {{
            "task_id": "task_1",
            "file_to_create": "utils.py",
            "initial_prompt": "Viết hàm cộng 2 số...",
            "test_command": "python -c \\"from utils import add; assert add(1,2)==3\\"",
            "max_loops": 3
        }}
    ]
    Yêu cầu dự án: {project_requirement}
    """
    
    raw_output = call_free_claude(prompt)
    
    match = re.search(r'\[.*\]', raw_output, re.DOTALL)
    if not match:
        print("Lỗi: Không tìm thấy JSON trong luồng trả về.")
        print("Output gốc:", raw_output)
        return
        
    tasks = json.loads(match.group(0))
    os.makedirs("tasks", exist_ok=True)
    
    print("\n--- KẾT QUẢ TẠO PLAN ---")
    for task in tasks:
        file_path = f"tasks/{task['task_id']}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(task, f, indent=4, ensure_ascii=False)
        print(f"✅ Đã tạo task: {file_path}")

if __name__ == "__main__":
    # Thiết lập giao diện dòng lệnh (CLI)
    parser = argparse.ArgumentParser(description="Tự động hóa chia Task cho free-claude-code")
    parser.add_argument(
        "-p", "--prompt", 
        type=str, 
        required=True, 
        help="Nội dung yêu cầu dự án bạn muốn tạo plan (Bọc trong dấu ngoặc kép)"
    )
    
    # Lấy tham số người dùng nhập vào
    args = parser.parse_args()
    
    # Gọi hàm với tham số đó
    generate_plan(args.prompt)