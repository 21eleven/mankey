import nbformat
import datetime
import sys
import os
import argparse

anki_dir = os.environ["ANKI_PROFILE"]

#model_map = {m[1]: m[0] for m in models}


def parse_notes(lns):
    return [n.split('\n') for n in
            '\n'.join(lns).split('---')[1:]]


def add_to_anki(doc, col=None):
    lines = doc.split('\n')

    deck = lines[1].strip()
    tags = (
        ['mankey', datetime.datetime.now().strftime("%Y%m%d-%H%M")]
        +
        lines[2].strip().split(' ')
    )

    #print(lines, deck, tags)
    print("-------------------------------------------")
    print(f"Deck: {deck}")

    notes = parse_notes(lines)
    for n in notes:
        print("~note~")
        del n[0]
        model = n[0]
        print(f"Model: {model}")
        if n[1] != '' or '####' not in n[1]:
            n_tags = tags + n[1].split(' ')
            print(f"Tags: {tags}")
            open_pre = 0
            idx = 0
            for ln in n:
                if ln:
                    if "```" in ln:
                        open_pre ^= 1
                        if open_pre:
                            html = "<pre>"
                        else:
                            html = "</pre>"
                        n[idx] = ln.replace('```', html)
                    if ln[:2] == "![":
                        # is image
                        pass
                    if ln[0] == "$":
                        n[idx] = "[latex]$"+ln.replace('$', '$[/latex]', 2)[9:]
                idx += 1

            fields = [''.join(f.split('\n', 1)[1:])
                      for f in '\n'.join(n).split('####')[1:]]
            for i in range(0, len(fields)):
                print(f"Field {i+1}")
                print(fields[i])
        if col:
            m_id = [k for (k, i) in col.models.models.items()
                    if i["name"] == model][0]

            m_id = model_map[model]
            col.decks.byName(deck)['mid'] = m_id
            note = col.newNote()
            note.model()['did'] = col.decks.byName(deck)['id']
            note.fields = fields
            note.tags = col.tags.canonify(
                col.tags.split(
                    ' '.join(n_tags).strip()
                )
            )
            m = note.model()
            m["tags"] = note.tags
            col.models.save(m)
            col.addNote(note)
    pass


def print_decks():
    import anki
    Collection = anki.storage.Collection
    col = Collection(f"{anki_dir}collection.anki2", log=True)
    print([d[1]["name"] for d in col.decks.decks.items()])
    col.save()
    del col


def print_models():
    import anki
    Collection = anki.storage.Collection
    col = Collection(f"{anki_dir}collection.anki2", log=True)
    print([(k, i['name']) for (k, i) in col.models.models.items()])
    col.save()
    del col


def test_parse(target):
    nb = nbformat.read(target, as_version=4)
    md_cells = [c['source'] for c in nb.cells if c['cell_type']
                == 'markdown' and '## anki\n' in c['source']]
    # return md_cells
    for md in md_cells:
        add_to_anki(md)


def parse(target):
    import anki
    Collection = anki.storage.Collection
    col = Collection(f"{anki_dir}collection.anki2", log=True)
    nb = nbformat.read(target, as_version=4)
    md_cells = [c['source'] for c in nb.cells if c['cell_type']
                == 'markdown' and '## anki\n' in c['source']]
    # return md_cells
    for md in md_cells:
        add_to_anki(md, col)
        break
    col.save()
    del col


def webparse(target):
    nb = nbformat.read(target, as_version=4)
    md_cells = [c['source'] for c in nb.cells if c['cell_type']
                == 'markdown' and '## anki\n' in c['source']]
    # return md_cells
    for md in md_cells:
        add_to_ankiweb(md)
        break


def add_to_ankiweb(md):
    from selenium import webdriver

    driver = webdriver.PhantomJS()

    driver.maximize_window()
    driver.get('https://ankiweb.net/account/login')
    driver.find_element_by_id('email').send_keys(os.environ["ANKIWEB_USER"])
    driver.find_element_by_id('password').send_keys(os.environ["ANKIWEB_PASS"])
    driver.find_element_by_xpath("//input[@value='Log in']").click()

    driver.get("https://ankiuser.net/edit/")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Mankey // Parses Anki notes from Jupyter Markdown')
    parser.add_argument("command", type=str, choices=[
                        'parse', 'test', 'decks', 'models'], )
    parser.add_argument(
        "-f", required=False, type=str, help="path to .md or .ipynb to test parse")
    args = parser.parse_args()
    print(args)
    if args.command == 'test':
        assert args.f != None
        test_parse(args.f)
    elif args.command == 'decks':
        print_decks()
    elif args.command == 'models':
        print_models()
