messages = [
    {'role': "assistant", "content":"SYSTEM_PROMPT"},
    {'role': "system", "content":"SYSTEM_PROMPT"},
    {'role': "user", "content":"SYSTEM_PROMPT"},
]

# for i, m in enumerate(messages):
#     role_color = {
#                 "system": "yellow",
#                 "user": "blue",
#                 "assistant": "green"
#             }.get(m["role"], "white")
    
#     print(role_color)

messages = [messages[0]]
print(type(messages))
