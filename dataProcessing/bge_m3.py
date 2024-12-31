from sentence_transformers import SentenceTransformer
 
def get_bge_m3_model():
    model = SentenceTransformer("BAAI/bge-m3", device="mps")
    return model
 
def get_bge_m3_embeddings(model, sentences):
    embeddings = model.encode(sentences)
    return embeddings

if __name__ == "__main__":

    model = get_bge_m3_model()

    sentences = [
        "Construction of reference to Ordinance, section, etc. (1) Any reference in any Ordinance to “any Ordinance” or to “any enactment” shall be construed as a reference to any Ordinance for the time being in force. (2) Where in an Ordinance there is a reference to a section or other division by number, letter or combination of number and letter, and not in conjunction with the title or short title of any other Ordinance, the reference shall be construed as a reference to the section or other division of that number, letter or combination in the Ordinance in which the reference occurs. (3) Where in a section of an Ordinance there is a reference to a subsection or other division by number, letter or combination of number and letter, and not in conjunction with the number of a section of that or any other Ordinance, the reference shall be construed as a reference to the subsection or other division of that number, letter or combination in the section in which the reference occurs. (4)-(5)",
        "Marginal notes and section headings (1) Where any section, subsection or paragraph of any Ordinance is taken verbatim from, or is substantially similar to, a section, subsection, paragraph or other provision of any law of a place outside Hong Kong or any treaty, there may be added as a note to the section, subsection or paragraph of the Ordinance a reference, in abbreviated form, to such section, subsection, paragraph or provision of that law or treaty. (2) A reference added under subsection (1) shall not have any legislative effect and shall not in any way vary, limit or extend the interpretation of any Ordinance. (3) A marginal note or section heading to any provision of any Ordinance shall not have any legislative effect and shall not in any way vary, limit or extend the interpretation of any Ordinance.",
        "Effect of repeal generally Where an Ordinance repeals in whole or in part any other Ordinance, the repeal shall not— (a) revive anything not in force or existing at the time at which the repeal takes effect; (b) affect the previous operation of any Ordinance so repealed or anything duly done or suffered under any Ordinance so repealed; (c) affect any right, privilege, obligation or liability acquired, accrued or incurred under any Ordinance so repealed; (d) affect any penalty, forfeiture or punishment incurred in respect of any offence committed against any Ordinance so repealed; or (e) affect any investigation, legal proceeding or remedy in respect of any such right, privilege, obligation, liability, penalty, forfeiture or punishment as aforesaid; and any such investigation, legal proceeding or remedy may be instituted, continued or enforced, and any such penalty, forfeiture or punishment may be imposed, as if the repealing Ordinance had not been passed.",
        "How to create a new ordinence?"
    ]
    embeddings = get_bge_m3_embeddings(model, sentences)

    print(embeddings)
    # similarities = model.similarity(embeddings[0], embeddings[3])
    # print(similarities)