
from app.core.stack import Stack

stack = Stack()

stack.push(10)
stack.push(20)
stack.push(30)

print("Stack:", stack.display())
print("Top element:", stack.peek())
print("Removed element:", stack.pop())
print("Stack after pop:", stack.display())
print("Stack size:", stack.size())
print("Is empty:", stack.is_empty())

