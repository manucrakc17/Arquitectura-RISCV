# alu.py

def execute_alu(operand_a, operand_b, alu_control):
    """
    Unidad Aritmético Lógica (ALU).
    Recibe dos operandos de 32 bits y un código de control.
    Devuelve el resultado de la operación.
    """
    # Forzar que los operandos se mantengan estrictamente en 32 bits
    operand_a = operand_a & 0xFFFFFFFF
    operand_b = operand_b & 0xFFFFFFFF

    # 1. Operación: SUMA (ALU Control 0000)
    if alu_control == "ADD":
        result = operand_a + operand_b

    # 2. Operación: RESTA (ALU Control 0001)
    elif alu_control == "SUB":
        result = operand_a - operand_b

    # 3. Operación: AND lógico (ALU Control 0010)
    elif alu_control == "AND":
        result = operand_a & operand_b

    # 4. Operación: OR lógico (ALU Control 0011)
    elif alu_control == "OR":
        result = operand_a | operand_b

    # 5. Operación: XOR lógico (ALU Control 0100)
    elif alu_control == "XOR":
        result = operand_a ^ operand_b

    # 6. Operación: Menor que (Set Less Than - SLT)
    elif alu_control == "SLT":
        # Convierte los operandos a enteros con signo para la comparación
        val_a = operand_a if operand_a < 0x80000000 else operand_a - 0x100000000
        val_b = operand_b if operand_b < 0x80000000 else operand_b - 0x100000000
        result = 1 if val_a < val_b else 0

    else:
        result = 0

    # Retornamos el resultado asegurando que calce en 32 bits
    return result & 0xFFFFFFFF