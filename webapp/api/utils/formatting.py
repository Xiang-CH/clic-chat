def format_ordinance(ordinances):
    return "\n\n".join([f"- **Cap {ord['cap_no']} ({ord['cap_title']}), {'Regulation' if ord['cap_no'][-1].isalpha() else 'Section'} {ord['section_no']} ({ord['section_heading']})**: {ord['text']}\n({ord['url']})" for ord in ordinances])

def format_judgement(judgements):
    return "\n\n".join([f"""- **{judge['date']}: {judge['case_name']} ({judge['court']})**: {judge['case_summary']}\n->Case Causes: {judge['case_causes']}\n->Court Decision: {judge['court_decision']}\n({judge['url']})""" for judge in judgements])