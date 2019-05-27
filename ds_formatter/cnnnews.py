import util as UTIL
from tqdm import tqdm

def parse_answer_token_ranges(answer_token_ranges):
    if answer_token_ranges == '':
        return [[]]
    return [[int(a) for a in b.split(':')] for b in answer_token_ranges.split(',')]

def anwer_range_to_span_index(context, ranges):
    """
    :param context: The context from the story, containing the answer
    :param answer_token_ranges: The index ranges mapping to the part of the context containg
                                the answer. It is a string, parsing needed
    :return: index pointing to the part of the context where the answer span starts.
    NewsQA stores the ranges as indexes over the tokenized context, SQuAD does it over 
    the characters index.
    """
    context_tokens = UTIL.word_tokenize(context)
    span_text = ' '.join(context_tokens[ranges[0]:ranges[1]])
    span_start = len(' '.join(context_tokens[:ranges[0]])) +1
    span_end = span_start + len(span_text)
    return span_start, span_end

def convert_to_squad(question_answer_content, context_content_path):
    """
    :param question_answer_content:
    :param context_content_path: story files folder path
    :return: formatted SQUAD data
    At initial version, we are just focusing on the context and question, nothing more,
    therefore we are ignoring the answer part as of now
    """
    # PARSE FILES
    import os

    squad_formatted_content = dict()
    squad_formatted_content['version'] = 'cnnnews_squad_format'
    data = []
    # group by story id (same context various questions)
    stories_gb = question_answer_content.groupby('story_id')
    # Columns: story_id, story_text, question, answer_token_ranges
    # skip answers with multiple ranges
    pbar = tqdm(total=question_answer_content.size)
    for story in stories_gb:
        qas = []
        paragraphs = []
        context = None
        # story[0] is the header, [1] contains the values
        for index, row in story[1].iterrows():
            pbar.update(1)
            ranges = parse_answer_token_ranges(row[3])
            if len(ranges) != 1:
                continue
            if not context:
                context = row[1].replace("''", '" ').replace("``", '" ')

            ranges = anwer_range_to_span_index(row[1], ranges[0])
            story_file_name = row[0][(row[0].rindex('/') + 1):] + '_' + str(index)

            # SQuAD 2.0 "is_impossible" field
            # TODO := How does unanswerable questions look like in newsqa?
            qas_ELEMENT = dict({
                'id': story_file_name,
                'question': row[2].replace("''", '" ').replace("``", '" '),
                'is_impossible': False,
                'answers': [{
                    'text': context[ranges[0]:ranges[1]],
                    'answer_start': ranges[0]
                }]
            })

            qas.append(qas_ELEMENT)

        if context is not None and len(qas) > 0:
            paragraphs.append(dict({
                'context': context,
                'qas': qas
            }))

            data.append(dict({
                'title': 'dummyTitle',
                'paragraphs': paragraphs
            }))

    squad_formatted_content['data'] = data

    return squad_formatted_content