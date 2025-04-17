# f = open("text.txt", "r")
# datas = f.readlines()
# # print(data)
# print(len(datas))
# if len(datas) > 0:
#     for data in datas:
#         new_data = data+"+1"
#         print(new_data)
# else:
#     print("it is breaking.....")

urls = []
try:
    with open('text.txt', 'r') as file:
        urls = file.readlines()
        urls = [url.strip() for url in urls if url.strip()]  # Remove any extra whitespace
    print(f"Read {len(urls)} URLs from the file.")
    for url in urls:
        print(url)

    
except Exception as e:
    print(f"Error reading the URL file: {e}")






