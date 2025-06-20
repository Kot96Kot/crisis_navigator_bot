import sys
from text_utils import trim_text


def main():
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r', encoding='utf-8') as f:
            text = f.read()
    else:
        text = sys.stdin.read()
    result = trim_text(text)
    sys.stdout.write(result)


if __name__ == "__main__":
    main()
