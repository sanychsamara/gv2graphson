import sys
import os
import json
import pydot

default_node_label = "concept"
default_edge_label = "parent"

edge_color_to_label_mapping = {
    # light brown
    "#cc9900": "",
    # black
    "#000000": "",
    # gray
    "#666666": "",
    "#808080": "",
    "#999999": "",
    "#b2b2b2": "",
    # green
    "#00cc00": "",
    "#00cc33": "",
    # blue
    "#0000ff": "",
    # red
    "#ff0000": "",
    "#ff3300": ""
}

edge_thickness_to_label_mapping = {
    "1": "",
    "2": "",
    "4": "next",
}

edge_style_to_label_mapping = {
    "solid": "",
    "dotted": "",
    "dashed": ""
}

node_shape_to_label_mapping = {
    "rect": "sequence",
    "hexagon": "english",
    "ellipse": "",
}

def main(gv_filename):

    if not os.path.exists(gv_filename):
        print("File '{0}' does not exist".format(gv_filename))
        return

    pydot_graph_container = pydot.graph_from_dot_file(gv_filename)

    graphson_nodes = {}

    # Internal structure of the graph returned by pydot library is weird
    # Graph has multiple dictionary-based container objects with 1 element inside
    # Graph also uses "obj_dict" intermediate dictionary for it's properties

    pydot_graph = pydot_graph_container[0]
    pydot_nodes = pydot_graph.obj_dict["nodes"]
    pydot_edges = pydot_graph.obj_dict["edges"]
    pydot_node_ids = pydot_graph.obj_dict["nodes"].keys()
    pydot_edge_ids = pydot_graph.obj_dict["edges"].keys()

    pydot_to_graphson_id_mappings = dict()

    # Converting nodes

    graphson_id = 0
    property_value_id = 0

    for pydot_node_id in pydot_node_ids:
        
        if pydot_node_id == "node":
            continue

        pydot_to_graphson_id_mappings[pydot_node_id] = graphson_id

        pydot_node = pydot_nodes[pydot_node_id][0]
        pydot_node_attributes = pydot_node["attributes"]

        graphson_node_name = pydot_node_attributes.get("xlabel")

        if graphson_node_name:
            graphson_node_name = graphson_node_name.strip('"')

        if not graphson_node_name:
            print("Node Id='{0}' has no label. Using Id instead.".format(pydot_node_id))
            graphson_node_name = pydot_node_id.strip('"')

        graphson_node = {} 
        graphson_node["id"] = graphson_id
        
        graphson_node_label = get_graphson_node_label(pydot_node_attributes)
        if graphson_node_label:
            graphson_node["label"] = graphson_node_label

        if graphson_node_name:
            graphson_node["properties"] = { 
                "name" : [ { 
                    "id" : property_value_id,
                    "value" : graphson_node_name 
                } ]
            }
            property_value_id += 1

        graphson_nodes[graphson_id] = graphson_node

        graphson_id += 1
        
    # Converting edges

    for pydot_edge_id in pydot_edge_ids:

        if pydot_edge_id == "edge":
            continue

        pydot_edge = pydot_edges[pydot_edge_id][0]
        pydot_edge_attributes = pydot_edge["attributes"]
        graphson_edge_label = pydot_edge_attributes.get("xlabel")
        
        graphson_edge = {} 
        graphson_edge["id"] = graphson_id
        
        graphson_edge_label = get_graphson_edge_label(pydot_edge_attributes)

        pydot_node_id_from = pydot_edge.get("points")[0]
        pydot_node_id_to = pydot_edge.get("points")[1]

        graphson_id_from = pydot_to_graphson_id_mappings[pydot_node_id_from]
        graphson_id_to = pydot_to_graphson_id_mappings[pydot_node_id_to]

        graphson_edge["inV"] = graphson_id_from
        graphson_edge["outV"] = graphson_id_to

        # from
        graphson_node_from = graphson_nodes[graphson_id_from]
        graphson_node_from_inE = graphson_node_from.get("inE", {})
        graphson_node_from_inE_ByLabel = graphson_node_from_inE.get(graphson_edge_label, [])

        graphson_node_from_inE_ByLabel.append(graphson_edge)
        
        graphson_node_from_inE[graphson_edge_label] = graphson_node_from_inE_ByLabel
        graphson_node_from["inE"] = graphson_node_from_inE
        graphson_nodes[graphson_id_from] = graphson_node_from

        # to
        graphson_node_to = graphson_nodes[graphson_id_to]
        graphson_node_to_outE = graphson_node_to.get("outE", {})
        graphson_node_to_outE_ByLabel = graphson_node_to_outE.get(graphson_edge_label, [])

        graphson_node_to_outE_ByLabel.append(graphson_edge)
    
        graphson_node_to_outE[graphson_edge_label] = graphson_node_to_outE_ByLabel
        graphson_node_to["outE"] = graphson_node_to_outE
        graphson_nodes[graphson_id_to] = graphson_node_to

        graphson_id += 1 

    graphson_filename_without_extension = os.path.splitext(gv_filename)[0]
    graphson_filename = graphson_filename_without_extension + ".json"

    with open(graphson_filename, 'w') as graphson_file:
        for graphson_node in graphson_nodes.values():
            #json.dump(graphson_node, graphson_file, indent=4)
            json.dump(graphson_node, graphson_file)
            graphson_file.write("\n")


def get_graphson_node_label(pydot_node_attributes):

    shape = pydot_node_attributes.get("shape")
    if shape:
        shape = shape.strip('"')
        node_label = node_shape_to_label_mapping.get(shape)
        if node_label:
            return node_label

    return default_node_label


def get_graphson_edge_label(pydot_edge_attributes):
    
    color = pydot_edge_attributes.get("color")
    if color:
        color = color.strip('"')
        edge_label = edge_color_to_label_mapping.get(color)
        if edge_label:
            return edge_label

    thickness = pydot_edge_attributes.get("penwidth")
    if thickness:
        thickness = thickness.strip('"')
        edge_label = edge_thickness_to_label_mapping.get(thickness)
        if edge_label:
            return edge_label

    style = pydot_edge_attributes.get("style")
    if style:
        style = style.strip('"')
        edge_label = edge_style_to_label_mapping.get(style)
        if edge_label:
            return edge_label

    return default_edge_label


if __name__ == "__main__":

    gv_filename = ""

    if len(sys.argv) > 1:
        gv_filename = sys.argv[1]

    if not gv_filename:
        gv_filename = "test_graph.gv"

    main(gv_filename)    