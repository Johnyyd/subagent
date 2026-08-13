import sys
import json
import subprocess
import re

def call_free_claude(prompt):
    result = subprocess.run(["free-claude-code", prompt], capture_output=True, text=True, encoding='utf-8')
    return result.stdout

def extract_code_block(text):
    """Trích xuất mã nguồn bên trong dấu ``` (markdown code block)"""
    match = re.search(r'```(?:[a-zA-Z]*)\n(.*?)```', text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip() # Trả về nguyên bản nếu không có backticks

def run_worker(task_file):
    with open(task_file, "r", encoding="utf-8") as f:
        task = json.load(f)
        
    current_prompt = task["initial_prompt"] + "\nChỉ trả về mã nguồn trong block ```code```, không giải thích gì thêm."
    file_to_create = task["file_to_create"]
    test_cmd = task["test_command"]
    
    for attempt in range(task["max_loops"]):
        print(f"\n[{task['task_id']}] Lần thử {attempt + 1}...")
        
        # 1. Gọi free-claude-code
        raw_output = call_free_claude(current_prompt)
        code_output = extract_code_block(raw_output)
        
        # 2. Lưu code ra file
        with open(file_to_create, "w", encoding="utf-8") as f:
            f.write(code_output)
            
        # 3. Chạy test command (kiểm tra code)
        print(f"[{task['task_id']}] Đang chạy test: {test_cmd}")
        result = subprocess.run(test_cmd, shell=True, capture_output=True, text=True)
        
        # 4. Kiểm tra (Feedback Loop)
        if result.returncode == 0:
            print(f"[{task['task_id']}] THÀNH CÔNG! Code pass bài test.")
            return
        else:
            error_log = result.stderr if result.stderr else result.stdout
            print(f"[{task['task_id']}] LỖI TỪ TEST:\n{error_log}")
            
            # Cập nhật prompt để bắt nó sửa lỗi
            current_prompt = f"""
            Đây là mã nguồn bạn vừa viết:
            ```
            {code_output}
            ```
            Khi chạy lệnh kiểm tra, nó văng ra lỗi sau:
            {error_log}
            
            Hãy tìm nguyên nhân và viết lại TOÀN BỘ file code đã sửa. CHỈ trả về code trong block ```.
            """
            
    print(f"[{task['task_id']}] THẤT BẠI sau {task['max_loops']} vòng lặp.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Sử dụng: python worker.py tasks/task_1.json")
        sys.exit(1)
    run_worker(sys.argv[1])