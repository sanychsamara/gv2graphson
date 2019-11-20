#  
# Copyright (c) Alexander Uslontsev. All rights reserved.  
# Licensed under the MIT License. See LICENSE file in the project root for full license information.  
#

import sys
import os
import json
import argparse
import pydot

# Default node label. Define here or use -n command line parameter.
default_node_label = "node"

# Default edge label. Define here or use -e command line parameter.
default_edge_label = "edge"

# Map edge color to edge label. 
# Define here or use -c command line parameter.
# List contains frequently used colors in Qt Visual Graph Editor
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

# Map edge thickness to edge label
# Define here or use -t command line parameter.
edge_thickness_to_label_mapping = {
    "1": "",
    "2": "",
    "4": "",
}

# Map edge drawing style to edge label
# Define here or use -s command line parameter.
edge_style_to_label_mapping = {
    "solid": "",
    "dotted": "",
    "dashed": ""
}

# Map node shape to node label
# Define here or use -p command line parameter.
node_shape_to_label_mapping = {
    "rect": "",
    "hexagon": "",
    "ellipse": "",
}

def main(gv_filename):

    if not os.path.exists(gv_filename):
        print("File '{0}' does not exist".format(gv_filename))
        return

    pydot_graph_container = pydot.graph_from_dot_file(gv_filename)

    # Internal structure of the graph returned by pydot library is weird
    # Graph has multiple dictionary-based container objects with 1 element inside
    # Graph also uses "obj_dict" intermediate dictionary for it's properties

    pydot_graph = pydot_graph_container[0]
    pydot_nodes = pydot_graph.obj_dict["nodes"]
    pydot_edges = pydot_graph.obj_dict["edges"]
    pydot_node_ids = pydot_graph.obj_dict["nodes"].keys()
    pydot_edge_ids = pydot_graph.obj_dict["edges"].keys()

    # When converting edges in second loop we will have access to GV NodeIDs only (arbitrary strings)
    # but to create a proper GraphSON edge we would need to know a newly created GraphSON NodeId (sequential integers)
    # This dictionary is filled in the first loop when converting edges

    pydot_to_graphson_id_mappings = dict()

    # --------------------------------
    # Converting nodes
    # --------------------------------

    graphson_nodes = {}    
    graphson_id = 0
    property_value_id = 0

    total_nodes_converted = 0
    total_edges_converted = 0

    for pydot_node_id in pydot_node_ids:
        
        # Pydot graph contains two nodes called 'node' and 'edge'
        # that define default visual attributes for nodes and edges
        # They are not part of the graph structure and should be ignored

        if pydot_node_id == "node" or pydot_node_id == "edge":
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
        total_nodes_converted += 1
        
    # --------------------------------
    # Converting edges
    # --------------------------------

    # In GV format edges are saved in a separate list (that's why there is a second loop)
    # In GraphSON format edges only exist as part of the nodes 

    for pydot_edge_id in pydot_edge_ids:

        pydot_edge = pydot_edges[pydot_edge_id][0]
        pydot_edge_attributes = pydot_edge["attributes"]
        
        graphson_edge = {} 
        graphson_edge["id"] = graphson_id
        
        graphson_edge_label = get_graphson_edge_label(pydot_edge_attributes)

        pydot_node_id_from = pydot_edge.get("points")[1]
        pydot_node_id_to = pydot_edge.get("points")[0]

        # Need to find GraphSON newly generated integer IDs
        # because internal dictionary of nodes 'graphson_nodes' uses GraphSON IDs
        graphson_id_from = pydot_to_graphson_id_mappings[pydot_node_id_from]
        graphson_id_to = pydot_to_graphson_id_mappings[pydot_node_id_to]

        # In == from
        # Out == to
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
        total_edges_converted += 1

    graphson_filename_without_extension = os.path.splitext(gv_filename)[0]
    graphson_filename = graphson_filename_without_extension + ".json"

    print("{0} nodes converted. {1} edges converted. Saving output file to '{2}'".format(total_nodes_converted, total_edges_converted, graphson_filename))

    with open(graphson_filename, 'w') as graphson_file:
        for graphson_node in graphson_nodes.values():
            json.dump(graphson_node, graphson_file)
            graphson_file.write("\n")


# Go through multiple override options and return final node label for GraphSON node
# At the moment only node shape can override label. 
# Color and style overrides for nodes are not supported (I do not use them at the moment - feel free to add)
def get_graphson_node_label(pydot_node_attributes):

    shape = pydot_node_attributes.get("shape")
    if shape:
        shape = shape.strip('"')
        node_label = node_shape_to_label_mapping.get(shape)
        if node_label:
            return node_label

    return default_node_label

# Go through multiple override options and return final edge label for GraphSON edge
def get_graphson_edge_label(pydot_edge_attributes):
    
    # "Color" attribute name is double quoted in my GV files
    color = pydot_edge_attributes.get("\"color\"")
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

# Adds or replaces "visual_attribute to label" mappings in one of the 4 default dictionary mappings
#   edge_color     to edge_label
#   edge_thickness to edge_label
#   edge_style     to edge_label
#   node_shape     to node_label

def add_override_mapping_from_params(default_mappings_dict, name_values_from_args):
    
    if not name_values_from_args:
        return
    
    params_mappings_dict = dict(name_value.split('=') for name_value in name_values_from_args)
    for key in params_mappings_dict.keys():
        default_mappings_dict[str(key)] = params_mappings_dict[key]
    

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--filename", help="Input filename in GraphViz DV format", required=True)
    parser.add_argument("-n", "--nodelabel", help="Node label. Defaults to 'node'.", default="node")
    parser.add_argument("-e", "--edgelabel", help="Edge label. Defaults to 'edge'.", default="edge")

    parser.add_argument("-c", "--edgecolor", help="Edge color to label mapping. Example: #cc9900=parent", action="append")
    parser.add_argument("-t", "--edgethickness", help="Edge thickness to label mapping. Example: 2=parent", action="append")
    parser.add_argument("-s", "--edgestyle", help="Edge style to label mapping. Example: dotted=parent", action="append")
    parser.add_argument("-p", "--nodeshape", help="Node shape to label mapping. Example: rect=person", action="append")

    # read arguments from the command line
    args = parser.parse_args()

    default_node_label = args.nodelabel
    default_edge_label = args.edgelabel

    # Override visual_attribute-to-label mappings via command line params
    add_override_mapping_from_params(edge_color_to_label_mapping, args.edgecolor)
    add_override_mapping_from_params(edge_thickness_to_label_mapping, args.edgethickness)
    add_override_mapping_from_params(edge_style_to_label_mapping, args.edgestyle)
    add_override_mapping_from_params(node_shape_to_label_mapping, args.nodeshape)


    main(args.filename)    