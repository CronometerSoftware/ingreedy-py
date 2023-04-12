from ingreedypy import Ingreedy
import traceback
from nltk import pos_tag
from nltk import word_tokenize
import logging
import pprint
import re

if logging.getLogger().hasHandlers():
    logging.getLogger().setLevel(logging.INFO)

pos_ignore_list = {"''", "(", ")", "--", ".", ":", "``", "SYM", "$"}


def add_search_words(parsed_object, description):


    logging.info("Analysing " + description)
    
    # remove stuff in parens
    description_wo_parens = re.sub(r'\([^)]*\)', ' ', description.lower().strip())
    if description_wo_parens is None or len(description_wo_parens) == 0:
        description_wo_parens = description

    choices_strings = description_wo_parens.split(" or ")
    choices = []
    for choice_string in choices_strings:
        this_choice = ""
        tokenised = word_tokenize(choice_string)
        if (tokenised is None or len(tokenised) == 0):
            continue
        for (word , pos) in pos_tag(tokenised):
            if pos in pos_ignore_list:
                continue

            this_choice = this_choice + " " + word

        choices.append(this_choice.strip())



    parsed_object['description'] = description
    parsed_object["choices"] = choices
    parsed_object['toTaste'] = "to taste" in description.lower()
    parsed_object['toServe'] = "to serve" in description.lower()
    parsed_object['saltAndPepper'] = "salt" in tokenised and "pepper" in tokenised
    return parsed_object

def has_serving(ingreedy_result):
    return ingreedy_result['quantity'] is not None and len(ingreedy_result['quantity']) > 0

def has_units(ingreedy_result):
    return has_serving(ingreedy_result) and ingreedy_result['quantity'][0]['unit'] is not None and len(ingreedy_result['quantity'][0]['unit'].strip()) != 0


def run_ingreedy_parse(to_parse):
    logging.info("Invoking ingreedy parser on " + to_parse)
    try:
        return Ingreedy().parse(to_parse.strip())
    except Exception as e: 
        without_parens = re.sub(r'\([^)]*\)', ' ', to_parse).strip()
        if len(without_parens) > 0:
            return Ingreedy().parse(without_parens)
        else:
            raise
    finally:
        logging.info("Ingreedy parser done") 


def cronometer_parse(ingredients):

    results = []
    for ing in ingredients:
        ing = ing.lower()
        logging.info("Working on ingredient " + ing)
        try: 
            if ing is None or ing == "":
                logging.info("skipping " + ing)
                continue
            ing = ing.replace(u'\xa0', u' ')

            
            parsed = run_ingreedy_parse(ing)
                 
            
            if not has_units(parsed) and re.search(r'\([^)]*\)', ing) is not None:
                logging.info("Ingreedy parse did not find units, removing parens and adding at start to try again.")
                content = re.search(r'\(([^)]*)\)', ing).group(1)
                new_attempt = run_ingreedy_parse(content + " " + re.sub(r'\([^)]*\)', ' ', ing))
                if (has_units(new_attempt)):
                    logging.info("Units found on second attempt, using this one!")
                    parsed = new_attempt
                else:
                    logging.info("Still no units found, using original")


            parsed_object = {'magnitude' : 1, 'raw': ing}
            if parsed['ingredient'] is not None and parsed['ingredient'] != "":
                parsed_object = add_search_words(parsed_object, parsed['ingredient'])
            if has_serving(parsed):
                if len(parsed['quantity']) > 1:
                    logging.info("multiple quantities " + str(parsed['quantity']) + " for " + ing)
                parsed_object['magnitude'] = parsed['quantity'][0]['amount']
                parsed_object['units'] = parsed['quantity'][0]['unit']
            else: 
                parsed_object['magnitude'] = "1"
                parsed_object['units'] = ""
            results.append(parsed_object)
            logging.info("Done with " + ing)
        except Exception as e: 
            #pass
            logging.error("ERROR WITH INGREDIENT: " + ing)
            traceback.print_exc()
        #eg. return format {'quantity': [{'unit': 'gram', 'unit_type': 'metric', 'amount': 200}], 'ingredient': 'mozzarella (or any other cheese), torn into pieces, for topping'}
    
    #TODO what if can't parse
    #TODO return multiple possible quantitites
    return results


if __name__ == "__main__":
    pp = pprint.PrettyPrinter(indent=4, width=100)
    print()
    print()
    pp.pprint(cronometer_parse(["a pinch of salt and pepper", "5g beans or waffles, crusty", "2 bottles of water", "water (56 ml), straight from the tap", "ham (about 3 cups)", "about 6 grams of ham", "approx 38 heads of lettuce", "6 pints butter (some nonesnese here that shouldn't appear in choices) well made"]))
