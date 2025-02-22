import asyncio
import json

from src.parser import InternshipsParser


async def main() -> None:
    async with InternshipsParser() as parser:  # noqa: F821
        data = await parser.get_total_data()

    with open('parser_results.json', 'w') as file:
        json.dump(data, file, ensure_ascii=False)

    print('Created parser_results.json!')


if __name__ == '__main__':
    asyncio.run(main())
