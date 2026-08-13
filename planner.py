import os
import json
import subprocess
import re
import argparse
import shlex

def call_free_claude(prompt, cli_cmd=None):
    if not cli_cmd:
        cli_cmd = os.getenv("CLAUDE_CMD", "fcc-claude")
    
    # Bọc prompt trong shlex.quote để an toàn tuyệt đối với mọi ký tự đặc biệt
    command = f'{cli_cmd} {shlex.quote(prompt)}'
    process = subprocess.run(command, shell=True, capture_output=True, text=True, encoding='utf-8')
    
    if process.returncode != 0:
        err_msg = process.stderr.strip() if process.stderr else "Lỗi không xác định"
        print(f"⚠️ Lỗi khi chạy lệnh CLI '{cli_cmd}' (Mã thoát: {process.returncode}):")
        print(f"   {err_msg}\n")
    
    return process.stdout


def generate_plan(project_requirement, cli_cmd=None):
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
    
    raw_output = call_free_claude(prompt, cli_cmd)
    
    match = re.search(r'\[.*\]', raw_output, re.DOTALL)
    if not match:
        print("❌ Lỗi: Không tìm thấy JSON trong luồng trả về.")
        print("Output gốc (stdout):", raw_output if raw_output.strip() else "(Rỗng - Hãy kiểm tra lệnh CLI hoặc trạng thái đăng nhập)")
        return
        
    try:
        tasks = json.loads(match.group(0))
    except json.JSONDecodeError as e:
        print(f"❌ Lỗi decode JSON: {e}")
        print("Nội dung tìm thấy:", match.group(0))
        return

    os.makedirs("tasks", exist_ok=True)
    
    print("\n--- KẾT QUẢ TẠO PLAN ---")
    for task in tasks:
        file_path = f"tasks/{task['task_id']}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(task, f, indent=4, ensure_ascii=False)
        print(f"✅ Đã tạo task: {file_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tự động hóa chia Task cho CLI AI")
    parser.add_argument(
        "-p", "--prompt", 
        type=str, 
        required=True, 
        help="Nội dung yêu cầu dự án bạn muốn tạo plan"
    )
    parser.add_argument(
        "-c", "--cmd",
        type=str,
        default=None,
        help="Lệnh CLI để gọi AI (mặc định dùng biến CLAUDE_CMD hoặc 'fcc-claude')"
    )
    
    args = parser.parse_args()
    generate_plan(args.prompt, cli_cmd=args.cmd)