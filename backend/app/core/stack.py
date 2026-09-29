
class Stack:

    def __init__(self):
        self.items = []

    # Insert element into stack
    def push(self, value):
        self.items.append(value)
        return value

    # Remove top element
    def pop(self):
        if self.is_empty():
            raise IndexError("Stack is empty")

        return self.items.pop()

    # View top element without removing it
    def peek(self):
        if self.is_empty():
            raise IndexError("Stack is empty")

        return self.items[-1]

    # Check whether stack is empty
    def is_empty(self):
        return len(self.items) == 0

    # Return stack size
    def size(self):
        return len(self.items)

    # Display stack elements
    def display(self):
        return self.items.copy()

    # Clear the stack
    def clear(self):
        self.items.clear()
