
import re
import math

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.stack import Stack

router = APIRouter()

FUNCTIONS = {"sin", "cos", "tan"}

OPENING = {"(", "[", "{"}

MATCHING = {
    ")": "(",
    "]": "[",
    "}": "{"
}


class CalculateRequest(BaseModel):
    expression: str
    angle_mode: str = "DEG"


# STEP 1: TOKENIZATION
def tokenize(expression):

    pattern = r"\d+(?:\.\d+)?|[A-Za-z]+|[+\-*/()]|[\[\]{}]|\s+|."

    tokens = re.findall(pattern, expression)

    result = []

    for token in tokens:

        if token.isspace():
            continue

        if token in FUNCTIONS:
            result.append(token)

        elif re.fullmatch(r"\d+(?:\.\d+)?", token):
            result.append(token)

        elif token in {"+", "-", "*", "/", "(", ")", "[", "]", "{", "}"}:
            result.append(token)

        else:
            raise ValueError(f"Invalid character or function: {token}")

    if not result:
        raise ValueError("Expression cannot be empty")

    return result


# STEP 2: INFIX TO POSTFIX
def infix_to_postfix(tokens):

    output = []
    operators = Stack()

    precedence = {
        "+": 1,
        "-": 1,
        "*": 2,
        "/": 2,
        "u+": 3,
        "u-": 3
    }

    right_associative = {"u+", "u-"}

    expect_operand = True

    for i, token in enumerate(tokens):

        # Numbers
        if re.fullmatch(r"\d+(?:\.\d+)?", token):

            if not expect_operand:
                raise ValueError("Missing operator between numbers")

            output.append(token)
            expect_operand = False

        # Trigonometric functions
        elif token in FUNCTIONS:

            if not expect_operand:
                raise ValueError("Missing operator before function")

            if i + 1 >= len(tokens) or tokens[i + 1] not in OPENING:
                raise ValueError(f"{token} requires parentheses")

            operators.push(token)
            expect_operand = True

        # Opening brackets
        elif token in OPENING:

            if not expect_operand:
                raise ValueError("Missing operator before bracket")

            operators.push(token)
            expect_operand = True

        # Closing brackets
        elif token in MATCHING:

            if expect_operand:
                raise ValueError("Invalid or empty brackets")

            expected_opening = MATCHING[token]

            while (
                not operators.is_empty()
                and operators.peek() not in OPENING
            ):
                output.append(operators.pop())

            if operators.is_empty():
                raise ValueError("Mismatched brackets")

            if operators.peek() != expected_opening:
                raise ValueError("Incorrectly matched brackets")

            operators.pop()

            # Apply function after its closing bracket
            if (
                not operators.is_empty()
                and operators.peek() in FUNCTIONS
            ):
                output.append(operators.pop())

            expect_operand = False

        # Arithmetic operators
        elif token in {"+", "-", "*", "/"}:

            if expect_operand:

                if token not in {"+", "-"}:
                    raise ValueError("Operator is missing an operand")

                token = "u" + token

            while not operators.is_empty():

                top = operators.peek()

                if top in OPENING or top in FUNCTIONS:
                    break

                higher_precedence = (
                    precedence[top] > precedence[token]
                )

                equal_left_associative = (
                    precedence[top] == precedence[token]
                    and token not in right_associative
                )

                if higher_precedence or equal_left_associative:
                    output.append(operators.pop())
                else:
                    break

            operators.push(token)
            expect_operand = True

    if expect_operand:
        raise ValueError("Expression ends with an operator")

    while not operators.is_empty():

        operator = operators.pop()

        if operator in OPENING:
            raise ValueError("Mismatched brackets")

        output.append(operator)

    return output


# STEP 3: POSTFIX EVALUATION USING STACK
def evaluate_postfix(postfix, angle_mode):

    stack = Stack()
    steps = []

    for token in postfix:

        # Push numbers
        if re.fullmatch(r"\d+(?:\.\d+)?", token):

            value = float(token)
            stack.push(value)

            steps.append({
                "token": token,
                "operation": "Push operand",
                "stack": stack.display()
            })

        # Unary operators
        elif token in {"u+", "u-"}:

            if stack.size() < 1:
                raise ValueError("Invalid expression")

            value = stack.pop()

            if token == "u-":
                value = -value

            stack.push(value)

            steps.append({
                "token": token,
                "operation": "Apply unary operator",
                "stack": stack.display()
            })

        # Trigonometric functions
        elif token in FUNCTIONS:

            if stack.size() < 1:
                raise ValueError("Invalid function expression")

            value = stack.pop()

            if angle_mode == "DEG":
                value = math.radians(value)

            if token == "sin":
                result = math.sin(value)

            elif token == "cos":
                result = math.cos(value)

            elif token == "tan":

                if abs(math.cos(value)) < 1e-12:
                    raise ValueError("Tangent is undefined at this angle")

                result = math.tan(value)

            stack.push(result)

            steps.append({
                "token": token,
                "operation": f"Calculate {token}",
                "stack": stack.display()
            })

        # Binary arithmetic
        else:

            if stack.size() < 2:
                raise ValueError("Invalid expression")

            b = stack.pop()
            a = stack.pop()

            if token == "+":
                result = a + b

            elif token == "-":
                result = a - b

            elif token == "*":
                result = a * b

            elif token == "/":

                if b == 0:
                    raise ValueError("Division by zero")

                result = a / b

            stack.push(result)

            steps.append({
                "token": token,
                "operation": f"Calculate {a} {token} {b}",
                "stack": stack.display()
            })

    if stack.size() != 1:
        raise ValueError("Invalid mathematical expression")

    result = stack.pop()

    # Remove floating-point display noise
    result = round(result, 12)

    if result == int(result):
        result = int(result)

    return result, steps


# STEP 4: CALCULATOR API
@router.post("/calculate")
def calculate(request: CalculateRequest):

    try:

        if request.angle_mode not in {"DEG", "RAD"}:
            raise ValueError("Angle mode must be DEG or RAD")

        tokens = tokenize(request.expression)

        postfix = infix_to_postfix(tokens)

        result, steps = evaluate_postfix(
            postfix,
            request.angle_mode
        )

        return {
            "status": "success",
            "expression": request.expression,
            "postfix": " ".join(postfix),
            "result": result,
            "angle_mode": request.angle_mode,
            "steps": steps
        }

    except (ValueError, OverflowError) as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )
