import os, shutil
import bibtexparser
import re
from wordcloud import STOPWORDS
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from datetime import datetime

class web_site_publications:
    def __init__(self):
        self.colors = {}
        self.ordering = {}

        self.colors["conference"] = "RoyalBlue"
        self.colors["proceedings"] = "Gold"
        self.colors["workshop"] = "Gray"
        self.colors["article"] = "Crimson"
        self.colors["phdthesis"] = "green"
        self.colors["bookchapter"] = "orange"
        self.colors["else"] = "black"

        self.ordering["conference"] = "[3]"
        self.ordering["proceedings"] = "[4]"
        self.ordering["workshop"] = "[6]"
        self.ordering["article"] = "[2]"
        self.ordering["phdthesis"] = "[1]"
        self.ordering["bookchapter"] = "[5]"
        self.ordering["else"] = "[9]"

        self.by_year = {}
        self.all_years = []
        self.num_entries = 0

    def get_key(self, keywords):
        if "conference" in keywords:
            return "conference"
        elif "proceedings" in keywords:
            return "proceedings"
        elif "workshop" in keywords:
            return "workshop"
        elif "article" in keywords:
            return "article"
        elif "phdthesis" in keywords:
            return "phdthesis"
        elif "bookchapter" in keywords:
            return "bookchapter"
        else:
            return "else"

    def read_bib(self, f_name):
        with open(f_name) as bibtex_file:
            bib_database = bibtexparser.load(bibtex_file)
        self.num_entries = len(bib_database.entries)
        for e in bib_database.entries:
            y = e["year"]
            if not y in self.by_year:
                self.all_years.append(y)
                self.by_year[y] = []
            self.by_year[y].append(e)


    def write_pub_site(self, f_out, filter, author_sites):
        with open(f_out, "w") as f:
            s_init = "+++\ndate = '2026-03-30T21:17:36+02:00'\ndraft = false\ntitle = 'Publications'\n+++\n"
            f.write(s_init)
            self.all_years.sort(reverse=True)

            f.write("<style>\ntable, th, td {\nborder: 0px;\npadding-top: 5px;\npadding-bottom: 5px;\npadding-left: 5px;\n"+
                    "padding-right: 5px;\n}\n</style>\n\n")

            f.write("<div style=\"text-align: center;\">\n  <img src=\"/images/venues.png\" alt=\"publication venues\" style=\"width:40vw;\">\n</div>\n\n")

            f.write("Filter by author:&nbsp; [all]({{< ref \"publications\" >}})\n")
            for author_name, file_name in author_sites:
                    f.write(" &nbsp; ■ &nbsp;\n[" + author_name + "]({{< ref \"" + file_name +"\" >}})\n")
            f.write("\n")

            i = self.count_filtered_refs(filter) # num of ref that fulfill the filter

            for y in self.all_years:
                # sort the entries
                sorted_entries = []
                for i_e in range(len(self.by_year[y])):
                    e = self.by_year[y][i_e]
                    key = self.get_key(e["keywords"])
                    do_not_add = not self.complies_filter(e, filter)
                    if do_not_add:
                        continue
                    sorted_entries.append((self.ordering[key],e))
                sorted_entries = sorted(sorted_entries, key=lambda x: x[0])
                if len(sorted_entries) == 0:
                    continue

                # write publications for this year
                f.write("### " + y + "\n")
                f.write("<table style=\"width:100%\">\n")
                for i_e in range(len(sorted_entries)):
                    _, e = sorted_entries[i_e]
                    key = self.get_key(e["keywords"])

                    # write number and dot
                    f.write("<tr valign=\"top\"><td><span style=\"color: " + self.colors[key] + ";\">■</span></td>")
                    f.write("<td>[" + str(i) + "]</td>")

                    f.write("<td>")
                    s = ""
                    if key == "conference" or key == "workshop" or key == "else":
                        s = self.format_conf(e)
                    elif key == "article":
                        s = self.format_journal(e)
                    elif key == "proceedings":
                        s = self.format_proceedings(e)
                    elif key == "bookchapter":
                        s = self.format_chapter(e)
                    elif key == "phdthesis":
                        s = self.format_thesis(e)
                    f.write(self.to_plain_txt(s))
                    if "award" in e:
                        f.write(", <strong style=\"color: red;\">" + e["award"] + "</strong>")
                    f.write(" (")
                    if "pdflocal" in e:
                        #f.write("[PDF](/papers/" + e["pdflocal"] + ")")
                        f.write("<a href=\"/papers/" + e["pdflocal"] + "\">PDF</a>, ")
                    elif "pdflink" in e:
                        f.write("<a href=\"" + e["pdflink"] + "\">PDF</a>, ")
                    f.write("<a href=\"../bibtex/" + e["ID"] + ".bib\">BibTeX</a>)")
                    i -= 1
                    f.write("</td>")
                    f.write("</tr>\n")
                f.write("</table>\n\n")

    def count_filtered_refs(self, filter) -> int:
        i = 0
        for y in self.all_years:
            for i_e in range(len(self.by_year[y])):
                e = self.by_year[y][i_e]
                if self.complies_filter(e, filter):
                    i += 1
        return i

    def complies_filter(self, e, filter) -> bool:
        do_not_add = True
        for f_key in filter:
            f_val = filter[f_key]
            key_enum = [f_key]
            if "[or]" in f_key:
                key_enum = f_key.split("[or]")
            found = False
            for k in key_enum:
                if k in e:
                    bib_text = self.to_plain_txt(e[k])
                    if f_val in bib_text:
                        found = True
                        break
            if not found:
                do_not_add = False
                break
        return do_not_add

    def get_name_link(self, n):
        return n

    def format_name(self, n):
        n = re.sub(r'\s+', ' ', n)
        nameList = n.split(" and ")
        res = nameList[0]
        for i in range(1, len(nameList)):
            if i < len(nameList) - 1:
                res += ", "
            elif len(nameList) > 2:
                res += ", and "
            else:
                res += " and "
            res += nameList[i]
        return res

    def format_conf(self, e):
        s = self.format_name(e["author"]) + ": "
        s += "<strong>" + e["title"] + ". </strong>"
        if "booktitle" in e:
            s += e["booktitle"] + ", "
        else:
            assert e["type"] == "Technical Report"
            s += "(Technical Report), "
        s += e["year"]
        if "pages" in e:
            s += ": " + e["pages"]
        return s

    def format_journal(self, e):
        s = self.format_name(e["author"]) + ": "
        s += "<strong>" + e["title"] + ". </strong>"
        s += e["journal"]
        if "volume" in e:
            s += " " + str(e["volume"])
        if "pages" in e:
            s += ": " + e["pages"]
        s += " (" + e["year"] + ")"
        return s

    def format_proceedings(self, e):
        s = self.format_name(e["editor"]) + ": "
        s += "<strong>" + e["title"] + ". </strong>"
        s += e["year"]
        return s

    def format_chapter(self, e):
        s = self.format_name(e["author"]) + ": "
        s += "<strong>" + e["title"] + ". </strong>"
        s += e["booktitle"] + " "
        s += e["year"]
        if "pages" in e:
            s += ": " + e["pages"].replace("--", "–")
        return s

    def format_thesis(self, e):
        s = self.format_name(e["author"]) + ": "
        s += "<strong>" + e["title"] + ". </strong>"
        s += "Dissertation Thesis, " + e["school"] + ", "
        s += e["year"]
        return s

    def to_plain_txt(self, s):
        s = s.replace(r"$\lambda$", "λ")
        s = s.replace(r"$h^Add$", "h-Add")
        s = s.replace(r"{\"{o}}", "ö")
        s = s.replace(r"{\"{u}}", "ü")
        s = s.replace(r"{\'{A}}", "Á")
        s = s.replace(r"{\'{a}}", "á")
        s = s.replace(r"{\'{e}}", "é")
        s = s.replace(r"{\v{s}}", "š")
        s = s.replace(r"({", "(")
        s = s.replace(r"})", ")")
        s = s.replace(r"--", "–")
        s = s.replace(r"{DSMC}", "DSMC")
        s = s.replace(r"{HTN}", "HTN")
        s = s.replace(r"{PandaDealer}", "PandaDealer")
        s = s.replace(r"{AAAI}", "AAAI")
        s = s.replace(r"{AI}", "AI")
        s = s.replace(r"{PANDA}", "PANDA")
        s = s.replace(r"{PCP}", "PCP")
        s = s.replace(r"{PDDL}", "PDDL")
        s = s.replace(r"{CFGs}", "CFGs")
        s = s.replace(r"{HDDL:}", "HDDL:")
        s = s.replace(r"{SAT}", "SAT")
        s = s.replace(r"\dots", "...")
        return s

    def create_conf_word_cl(self, f_wc):
        # https://www.geeksforgeeks.org/python/generating-word-cloud-python/
        words = []
        key = "confacronym"
        for y in self.all_years:
            for e in self.by_year[y]:
                if key in e:
                    words.append(e[key])
        text = ' '.join(words)
        text = re.sub(r'[^A-Za-z\s]', '', text)
        #text = text.lower()
        stopwords = set(STOPWORDS)
        text = ' '.join(word for word in text.split() if word not in stopwords)
        wordcloud = WordCloud(width=800, height=400, background_color='white', colormap="Blues_r").generate(text) # bone, Blues, Blues_r

        plt.figure(figsize=(10, 5))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        #plt.title("Publication Venues")
        #plt.show()
        plt.savefig(f_wc, bbox_inches='tight')

    def create_research_wc(self, param):
        words = []
        key = "abstract"
        current_year = datetime.now().year
        for y in self.all_years:
            if current_year - int(y) > 5:
                continue
            for e in self.by_year[y]:
                if key in e:
                    words.append(e[key])
        for y in self.all_years:
            for e in self.by_year[y]:
                if key in e:
                    words.append(e[key])
        text = ' '.join(words)
        text = re.sub(r'[^A-Za-z\s]', '', text)
        #text = text.lower()
        stopwords = set(STOPWORDS)
        text = ' '.join(word for word in text.split() if word not in stopwords)
        wordcloud = WordCloud(width=800, height=400, background_color='white', colormap="Blues_r").generate(text) # bone, Blues, Blues_r

        plt.figure(figsize=(10, 5))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        #plt.title("Publication Venues")
        #plt.show()
        #plt.savefig(f_wc, bbox_inches='tight')

    def write_bibtex_files(self, target_dir):
        # delete old bibtex files
        for filename in os.listdir(target_dir):
            file_path = os.path.join(target_dir, filename)
            try:
                if filename.endswith(".bib") and (os.path.isfile(file_path) or os.path.islink(file_path)):
                    os.unlink(file_path)
            except Exception as e:
                print('Failed to delete %s. Reason: %s' % (file_path, e))
        for y in self.all_years:
            for e in self.by_year[y]:
                bib_name = os.path.join(target_dir, e["ID"] + ".bib")
                with open(bib_name, "w") as f:
                    f.write("@" + e["ENTRYTYPE"] + "{" +  e["ID"] + ",\n")
                    entries = []
                    for k in ["title", "author", "editor", "booktitle", "publisher", "journal", "volume", "series",
                              "school", "institution", "type", "chapter", "pages", "doi", "year"]:
                        if k in e:
                            entries.append((k, e[k]))
                    for i in range(len(entries)):
                        k, v = entries[i]
                        f.write("   " + k + " = {" + v + "}")
                        if i < len(entries) - 1:
                            f.write(",")
                        f.write("\n")
                    f.write("}")


if __name__ == '__main__':
    pub = web_site_publications()
    pub.read_bib("bibliography.bib")
    base_path = "/home/dh/Source-Code/np-website/quickstart/"

    #
    # write publication sites
    #
    author_pub_sites = [('Daniel Höller', 'publicationsHoeller.md'),
                        ('Marcel Schubert', 'publicationsSchubert.md'),
                        ('Jonas Kück', 'publicationsKrueck.md'),
                        ('Magnus Cunow', 'publicationsCunow.md')]

    pub.write_pub_site(os.path.join(base_path, "content", "publications.md"), filter=dict(), author_sites=author_pub_sites)
    for author, f_name in author_pub_sites:
        filter = {'author[or]editor': author}
        abs_f_name = os.path.join(base_path, "content", f_name)
        pub.write_pub_site(abs_f_name, filter, author_sites=author_pub_sites)

    pub.write_bibtex_files(os.path.join(base_path, "static/bibtex"))
    #
    # write word clouds
    #
    pub.create_conf_word_cl(os.path.join(base_path, "static/images/venues.png"))
    # pub.create_research_wc(os.path.join(base_path, "static/images/research.png"))

