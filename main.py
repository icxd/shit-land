from typing import Callable
from enum import Enum, auto

class Op(Enum):
    OP_PUSH_INT = auto()
    OP_PLUS = auto()
    OP_MINUS = auto()
    OP_DUMP = auto()

    def __str__(self) -> str: return self.name
    def __repr__(self) -> str: return self.name

def find_col(line: str, start: int, predecate: Callable[[str], bool]) -> int:
    while start < len(line) and not predecate(line[start]):
        start += 1
    return start

def lex_line(line: str) -> None:
    col: int = find_col(line, 0, lambda x: not x.isspace())
    while col < len(line):
        col_end: int = find_col(line, col, lambda x: x.isspace())
        yield (col, line[col:col_end])
        col = find_col(line, col_end, lambda x: not x.isspace())

def lex_file(file: str) -> None:
    with open(file, 'r') as f:
        return [(file, row, col, token)
                for (row, line) in enumerate(f.readlines())
                for (col, token) in lex_line(line)]
    
def parse_token_as_op(token: str) -> tuple[Op, ...]:
    if token == '+':
        return (Op.OP_PLUS, )
    elif token == '-':
        return (Op.OP_MINUS, )
    elif token == '.':
        return (Op.OP_DUMP, )
    else:
        try:
            return (Op.OP_PUSH_INT, int(token))
        except ValueError:
            raise Exception(f"Invalid token {token}")

def parse_file(file: str) -> list[tuple[Op, ...]]:
    ops: list[tuple[Op, ...]] = []
    for (file, row, col, token) in lex_file(file):
        try:
            ops.append(parse_token_as_op(token))
        except Exception as e:
            print(f"Error at %s:%d:%d: %s" % (file, row + 1, col + 1, e))
            return []
    return ops

def compile_ops(ops: list[tuple[Op, ...]]) -> str:
    out: str = "BITS 64\n"
    out += "segment .text\n"
    out += "dump:\n"
    out += "    mov     r9, -3689348814741910323\n"
    out += "    sub     rsp, 40\n"
    out += "    mov     BYTE [rsp+31], 10\n"
    out += "    lea     rcx, [rsp+30]\n"
    out += ".L2:\n"
    out += "    mov     rax, rdi\n"
    out += "    lea     r8, [rsp+32]\n"
    out += "    mul     r9\n"
    out += "    mov     rax, rdi\n"
    out += "    sub     r8, rcx\n"
    out += "    shr     rdx, 3\n"
    out += "    lea     rsi, [rdx+rdx*4]\n"
    out += "    add     rsi, rsi\n"
    out += "    sub     rax, rsi\n"
    out += "    add     eax, 48\n"
    out += "    mov     BYTE [rcx], al\n"
    out += "    mov     rax, rdi\n"
    out += "    mov     rdi, rdx\n"
    out += "    mov     rdx, rcx\n"
    out += "    sub     rcx, 1\n"
    out += "    cmp     rax, 9\n"
    out += "    ja      .L2\n"
    out += "    lea     rax, [rsp+32]\n"
    out += "    mov     edi, 1\n"
    out += "    sub     rdx, rax\n"
    out += "    xor     eax, eax\n"
    out += "    lea     rsi, [rsp+32+rdx]\n"
    out += "    mov     rdx, r8\n"
    out += "    mov     rax, 1\n"
    out += "    syscall\n"
    out += "    add     rsp, 40\n"
    out += "    ret\n"
    out += "global _start\n"
    out += "_start:\n"
    for op in ops:
        (op, *args) = op
        match op:
            case Op.OP_PUSH_INT:
                out += "    ;; -- push %d --\n" % args[0]
                out += "    push %d\n" % args[0]
            case Op.OP_PLUS:
                out += "    ;; -- add --\n"
                out += "    pop rax\n"
                out += "    pop rbx\n"
                out += "    add rax, rbx\n"
                out += "    push rax\n"
            case Op.OP_MINUS:
                out += "    ;; -- sub --\n"
                out += "    pop rax\n"
                out += "    pop rbx\n"
                out += "    sub rbx, rax\n"
                out += "    push rbx\n"
            case Op.OP_DUMP:
                out += "    ;; -- dump --\n"
                out += "    pop rdi\n"
                out += "    call dump\n"
            case _:
                raise Exception("Invalid op %s" % op)
    out += "    ;; -- exit --\n"
    out += "    mov rax, 60\n"
    out += "    mov rdi, 0\n"
    out += "    syscall\n"
    return out

def main() -> None:
    from sys import argv
    if len(argv) < 2:
        print("Usage: main.py <file>")
        return
    ops: list[tuple[Op, ...]] = parse_file(argv[1])
    print(ops)
    if len(ops) == 0:
        return
    try:
        out: str = compile_ops(ops)
        with open("out.asm", 'w') as f:
            f.write(out)
        print("Compiled to out.asm")
        import subprocess
        print("Running nasm...")
        subprocess.run(["nasm", "-felf64", "out.asm"])
        print("Linking...")
        subprocess.run(["ld", "-o", "out", "out.o"])
        print("Running...")
        subprocess.run(["./out"])
    except Exception as e:
        print(e)

if __name__ == '__main__':
    main()