
# This function converts a byte size into a human readable format.
def format_unit_4_byte_size(bytes: int) -> dict:
    units = ["bytes", "KB", "MB", "GB", "TB"]
    index = 0
    size = float(bytes)
    
    while size >= 1024 and index < len(units) - 1:
        size /= 1024
        index += 1
    
    return { "value": round(size, 2), "unit": units[index]}

# # Usage example:
# size_kb = 3056780
# formatted_size = format_unit_4_byte_size(size_kb)
# print(formatted_size)  # Output: "2.92 GB"
