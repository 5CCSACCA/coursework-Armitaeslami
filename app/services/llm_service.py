class LlmService:
    def generate_description(self, object_counts):
        # if no objects were detected
        if len(object_counts) == 0:
            return "I did not detect anything in the image."

        # make parts of the sentence
        parts_of_sentence = []

        for object_name, number_found in object_counts.items():
            if number_found == 1:
                parts_of_sentence.append("1 " + object_name)
            else:
                parts_of_sentence.append(str(number_found) + " " + object_name + "s")

        # connect the parts with the word "and"
        final_sentence = " and ".join(parts_of_sentence)

        return "There are " + final_sentence + " in the picture."
