def print_progress_bar(prefix='Progress: ', current=0, length=1):
    # Obviously if length is 10,000 or something we can't render that. The average terminal window
    # is 80col x 24row; let's use 50 col.
    bar_length = 50

    # Meat of the bar
    percent = current/length
    num_blocks = int(percent * bar_length)
    num_dash = bar_length - num_blocks
    blocks = "█" * num_blocks
    dashes = "-" * num_dash

    # End of the bar
    suffix = "| {:.2f}%".format(percent * 100)

    # Print it out with print. I'd use logger, but getting logger to print carriage return only is painful
    print("\r" + prefix + "|" + blocks + dashes + suffix, end="", flush=True)

    # Print newline if done
    if current == length:
        print()
