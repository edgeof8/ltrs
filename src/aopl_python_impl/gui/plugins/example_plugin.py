# Example Cosmic Scratchpad Plugin

def word_count_handler(context, node, calculator):
    """Counts the words in the expression of the last evaluated node."""
    last_node = node.scene.last_evaluated_calc_node
    if last_node:
        word_count = len(last_node.expression_str.split())
        output = f"The last expression had {word_count} words."
        node.set_display(output, False, is_command_output=True)
    else:
        node.set_display("Error: No previous calculation found.", True, is_command_output=True)

def register():
    """Returns a dictionary of commands to register."""
    return {
        "/wordcount": word_count_handler
    }
