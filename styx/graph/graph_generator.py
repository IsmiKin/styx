import fire
import ujson
import networkx as nx
import matplotlib.pyplot as plt


def generate_graph(graph_data, output_filename):
    G = nx.Graph()

    for node in graph_data["nodes"]:
        G.add_node(node["id"])

    for link in graph_data["links"]:
        G.add_edges_from([(link["source"], link["target"])])

    # TODO: improve this below to something more pythonist
    labeldict = {node["id"]: node["name"] for node in graph_data["nodes"]}

    nx.draw(G, labels=labeldict, with_labels=True)

    if output_filename:
        plt.savefig(output_filename)

    return True


def run(file_dir, output_filename):
    with open(file_dir, "r") as file_data:
        graph_data = ujson.load(file_data)
        generate_graph(graph_data, output_filename)

        return "Plot generated on {}".format(output_filename)


# example full run
# python graph_generator.py run graph_data_report.json graphita_.png
if __name__ == "__main__":
    fire.Fire()
