import os
import json
import re
import markdown
from bs4 import BeautifulSoup

def generate_recipe(md_path):
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()
        html_content = markdown.markdown(content)

        soup = BeautifulSoup(html_content, 'html.parser')

        # 找到 <h1> 和第一个 <h2> 之间的所有 <p> 标签作为描述
        description = []
        h1 = soup.find('h1')
        first_h2 = soup.find('h2')

        if h1 and first_h2:
            for tag in h1.find_all_next():
                if tag == first_h2:
                    break
                if tag.name == 'p':
                    text = tag.get_text(strip=True)
                    if text:  # 排除空段落
                        if "预估烹饪难度：" in text:
                            difficulty_text = text.split("预估烹饪难度：")[1].strip()
                            difficulty = len(difficulty_text)
                        else:
                            description.append(text)


        # 提取原料列表
        ingredients_section = soup.find('h2', string='必备原料和工具')
        ingredients = []
        if ingredients_section:
            ul = ingredients_section.find_next('ul')
            ingredients = [li.get_text(strip=True) for li in ul.find_all('li')]

        # 提取计算部分
        calculation_section = soup.find('h2', string='计算')
        calculation = []
        if calculation_section:
            ul = calculation_section.find_next('ul')
            calculation = [li.get_text(strip=True) for li in ul.find_all('li')]

        # 提取操作步骤
        steps_section = soup.find('h2', string='操作')
        steps = []

        if steps_section:
            # 尝试查找 <ul> 或 <ol> 列表
            list_tag = steps_section.find_next(['ul', 'ol'])
            if list_tag:
                steps = [li.get_text(strip=True) for li in list_tag.find_all('li')]

        extra_items = []
        extra_section_found = False

        for line in content.splitlines():
            if re.match(r'#+\s*附加内容', line):
                extra_section_found = True
                continue
            if extra_section_found:
                if re.match(r'#+\s*\S+', line) or re.match(r'如果您遵循本指南的制作流程而发现有问题或可以改进的流程', line):
                    extra_section_found = False
                    break
                if line.strip():  # 非空行
                    line = line.replace("- ", "").replace("* ", "").replace("+ ", "")
                    line = re.sub(r'^\d+\.\s*', '', line)
                    extra_items.append(line.strip())

        # 输出结果
        result = {
            '描述': description,
            '预估烹饪难度': difficulty,
            '原料和工具': ingredients,
            '食材计算': calculation,
            '操作步骤': steps,
            '附加内容': extra_items,
        }
        return result

if __name__ == "__main__":
    print("开始生成菜谱 JSON 文件...")

    # 提取 ignore 菜单
    with open('ignore.json', 'r', encoding='utf-8') as f:
        ignore_dish_list = json.load(f)
    print(f"忽略以下菜谱：{ignore_dish_list}")

    result = {}
    filtered_result = {}
    categories = os.listdir('dishes')
    for category_name in categories:
        result[category_name] = {}
        filtered_result[category_name] = {}
        dishes = os.listdir(os.path.join('dishes', category_name))
        for dish_name in dishes:

            if not (os.path.isdir(os.path.join('dishes', category_name, dish_name))) and dish_name.endswith('.md'):
                recipe = generate_recipe(os.path.join('dishes', category_name, dish_name))
                result[category_name][dish_name.replace('.md', '')] = recipe
                if dish_name not in ignore_dish_list:
                    filtered_result[category_name][dish_name.replace('.md', '')] = recipe

            elif os.path.isdir(os.path.join('dishes', category_name, dish_name)):
                sub_dishes = os.listdir(os.path.join('dishes', category_name, dish_name))
                for sub_dish in sub_dishes:
                    if sub_dish.endswith('.md'):
                        recipe = generate_recipe(os.path.join('dishes', category_name, dish_name, sub_dish))
                        result[category_name][sub_dish.replace('.md', '')] = recipe
                        if dish_name not in ignore_dish_list:
                            filtered_result[category_name][dish_name.replace('.md', '')] = recipe
            else:
                continue

    with open('recipes.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=4)
    print("菜谱 JSON 文件生成完毕，保存在 recipes.json")

    with open('filtered_recipes.json', 'w', encoding='utf-8') as f:
        json.dump(filtered_result, f, ensure_ascii=False, indent=4)
    print("过滤后的菜谱 JSON 文件生成完毕，保存在 filtered_recipes.json")