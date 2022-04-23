# symbol * means any symbol, returns -1 if not found


class ParseError(BaseException):
    pass


def find_pattern(string: str, pattern: str, cur_pos=0) -> int:
    n = len(string)
    n2 = len(pattern)

    if cur_pos >= n - n2:
        return -1

    for i in range(cur_pos, n - n2 + 1):
        str_part = string[i:i + n2]
        total_cmp = 0
        for k in range(n2):
            if str_part[k] == pattern[k] or pattern[k] == "*":
                total_cmp += 1
                continue
        if total_cmp == n2:  # found pattern
            return i

    return -1


def replace_string(string: str, rep: str, position: int, size=None) -> str:
    if not size:
        size = len(rep)

    return string[:position] + rep + string[position + size:]


def process_in_out_tag(string: str, in_: str, out: str, html_in: str, html_out: str):
    original_string = string

    header_entry = find_pattern(string, in_)
    if header_entry == -1:
        return string

    total_entries = 0
    while header_entry != -1:
        string = replace_string(string, html_in, header_entry, len(in_))
        header_entry = find_pattern(string, in_, header_entry + 1)
        total_entries += 1

    header_out = find_pattern(string, out)
    total_out = 0

    if header_out == -1:
        return original_string

    while header_out != -1 and total_out < total_entries:
        string = replace_string(string, html_out, header_out, len(out))
        header_out = find_pattern(string, out, header_out)
        total_out += 1

    return string


def process_link_tags(string: str) -> str:
    original_string = string
    result = string

    link_entry = find_pattern(result, "[LINK name=")
    while link_entry != -1:
        link_name_entry = link_entry + 12
        link_name_entry_char = result[link_name_entry - 1]
        link_name_out = find_pattern(result, link_name_entry_char, link_name_entry)

        if link_name_out == -1:
            raise ParseError(
                f"Unclosed link name starts with{result[link_name_entry:min(link_name_entry + 10, len(result))]}!")

        link_name = result[link_name_entry:link_name_out]

        url_entry = find_pattern(result, "url=", link_name_entry)
        url_entry_char = result[url_entry + 4]

        if url_entry == -1:
            raise ParseError(f"Cannot find url in link with name{link_name}!")

        url_out = find_pattern(result, url_entry_char, url_entry + 5)

        if url_out == -1:
            raise ParseError(
                f"Unclosed url starts with{result[url_entry:min(url_entry + 10, len(string))]}!")

        url = result[url_entry + 5:url_out]
        tag_out = find_pattern(result, "]", url_out)
        tag_length = tag_out - link_entry + 1

        result = replace_string(result, f'<a href="{url}">{link_name}</a>', link_entry, tag_length)

        link_entry = find_pattern(result, "[LINK name=")

    return result


def process_img_tags(string: str, replaces: dict) -> str:
    original_string = string
    result = string

    img_entry = find_pattern(result, "[IMG name=")
    while img_entry != -1:
        img_name_entry = img_entry + 11
        img_name_entry_char = result[img_name_entry - 1]
        img_name_out = find_pattern(result, img_name_entry_char, img_name_entry)

        if img_name_out == -1:
            raise ParseError(
                f"Unclosed link name starts with{result[img_name_entry:min(img_name_entry + 10, len(result))]}!")

        img_name = result[img_name_entry:img_name_out]
        tag_out = find_pattern(result, "]", img_name_entry)
        tag_length = tag_out - img_entry + 1
        # do name to url converting here
        result = replace_string(result, f'<img src="{replaces[img_name]}" style="max-width: 100%"', img_entry, tag_length)

        img_entry = find_pattern(result, "[IMG name=")

    return result


def process_video_tags(string: str, replaces) -> str:
    original_string = string
    result = string

    img_entry = find_pattern(result, "[VIDEO name=")
    while img_entry != -1:
        img_name_entry = img_entry + 13
        img_name_entry_char = result[img_name_entry - 1]
        img_name_out = find_pattern(result, img_name_entry_char, img_name_entry)

        if img_name_out == -1:
            raise ParseError(
                f"Unclosed link name starts with{result[img_name_entry:min(img_name_entry + 10, len(result))]}!")

        img_name = result[img_name_entry:img_name_out]
        tag_out = find_pattern(result, "]", img_name_entry)
        tag_length = tag_out - img_entry + 1
        # do name to url converting here
        result = replace_string(result, f'<video src="{replaces[img_name]}" style="width: 50%" controls></video>', img_entry, tag_length)

        img_entry = find_pattern(result, "[VIDEO name=")

    return result


def process_color_tags(string: str) -> str:
    original_string = string
    result = string

    color_entry = find_pattern(result, "[COLOR #******]")
    while color_entry != -1:
        text_entry = color_entry + 15
        text_out = find_pattern(result, "[/COLOR]")

        if text_out == -1:
            raise ParseError(f"Cannot find closing [/COLOR] tag! Starts width{result[color_entry:color_entry + 15]}")

        result = replace_string(result,
                                f'<span style="color: #{result[color_entry + 8: color_entry + 14]}">'
                                f'{result[text_entry:text_out]}</span>', color_entry, text_out - color_entry + 8)

        color_entry = find_pattern(result, "[COLOR #******]")

    return result


def process_hr_tags(string: str) -> str:
    result = string

    hr_entry = find_pattern(result, "[HR]")
    while hr_entry != -1:
        result = replace_string(result, "<hr>", hr_entry, 4)
        hr_entry = find_pattern(result, "[HR]")

    return result


def parse(string, replaces, ignore_img=False):
    result = process_in_out_tag(string, "[H]", "[/H]", "<h1>", "</h1>")
    result = process_in_out_tag(result, "[I]", "[/I]", "<i>", "</i>")
    result = process_in_out_tag(result, "[CODE]", "[/CODE]", '<div style="background-color: #f5f5f5; border: 1px solid #d5d5d5; border-radius: 3px; line-height: normal;" class="px-3 py-1 my-3 w-50"><code>', "</code></div>")
    result = process_in_out_tag(result, "[B]", "[/B]", "<b>", "</b>")
    result = process_hr_tags(result)
    result = process_link_tags(result)
    if not ignore_img:
        result = process_img_tags(result, replaces)
        result = process_video_tags(result, replaces)
    result = process_color_tags(result)
    result = result.replace('\n', '<br>')

    return result
