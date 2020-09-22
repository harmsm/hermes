
from matplotlib import pyplot as plt

SMALL_SIZE = 20
MEDIUM_SIZE = 22
BIGGER_SIZE = 24
BACKGROUND_COLOR = (54/255,57/255,63/255)
ELEMENT_COLOR = "white"
ACCENT_COLOR = (57/255,150/255,219/255)

plt.rc('font', size=SMALL_SIZE)          # controls default text sizes
plt.rc('axes', titlesize=SMALL_SIZE)     # fontsize of the axes title
plt.rc('axes', labelsize=MEDIUM_SIZE)    # fontsize of the x and y labels
plt.rc('xtick', labelsize=SMALL_SIZE)    # fontsize of the tick labels
plt.rc('ytick', labelsize=SMALL_SIZE)    # fontsize of the tick labels
plt.rc('legend', fontsize=SMALL_SIZE)    # legend fontsize
plt.rc('figure', titlesize=BIGGER_SIZE)  # fontsize of the figure title
plt.rc('figure',facecolor=BACKGROUND_COLOR)
plt.rc('axes',facecolor=BACKGROUND_COLOR)

plt.rc("xtick",color=ELEMENT_COLOR)
plt.rc("ytick",color=ELEMENT_COLOR)
plt.rc("axes",labelcolor=ELEMENT_COLOR)
plt.rc("axes",edgecolor=ELEMENT_COLOR)

def _wrap_string(some_string,soft_wrap_length=4):
    """
    Do a soft wrap of strings at space breaks.
    """

    fields = some_string.split()
    lengths = [len(f) for f in fields]
    wrapped = [[fields[0]]]
    current_total = lengths[0] + 1
    for i in range(1,len(lengths)):
        if current_total >= soft_wrap_length:
            wrapped.append([])
            current_total = 0

        wrapped[-1].append(fields[i])
        current_total += lengths[i] + 1

    out = []
    for w in wrapped:
        out.append(" ".join(w))
    out = "\n".join(out)

    return out

def plot_and_save(count_dict,title,file_root):
    """
    Generate a pretty barplot of poll results and save as a png and csv file.
    """

    names = count_dict.keys()
    pretty_names = [_wrap_string(n) for n in names]
    height = list(count_dict.values())

    # Generate plot
    fig, ax = plt.subplots(figsize=(8,6))
    plt.bar(pretty_names,height,width=0.95,color=ACCENT_COLOR)

    # Add numbers above each bar
    vertical_offset = sum(height)/len(height)*0.08
    for i in range(len(height)):
        plt.text(x=i,
                 y=height[i] + vertical_offset,
                 s=f"{height[i]}",ha="center",fontsize=BIGGER_SIZE,
                 color=ELEMENT_COLOR)

    # Deal with axes and title
    ax.set_ylim(0,max(height)*1.1)
    fig.suptitle(_wrap_string(title,25),color=ELEMENT_COLOR)
    ax.set_ylabel("votes")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["bottom"].set_visible(False)

    # Clean up layout
    fig.tight_layout()

    # Save image file
    fig.savefig(f"{file_root}.png",facecolor=BACKGROUND_COLOR)

    # Write out results as a csv file
    f = open(f"{file_root}.csv","w")
    f.write(f"# {title}\n")
    for i in range(len(pretty_names)):
        f.write(f"{pretty_names[i]},{height[i]}")
    f.close()
