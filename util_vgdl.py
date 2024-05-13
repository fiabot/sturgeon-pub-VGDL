import util_common
import networkx as nx 
import util_graph 
import re 
import csv 

def get_indent(line):
    
    indent = re.match(r"\s*", line).group()
    return len(indent)

def get_subsection(line):
    subsection = ""
    if("SpriteSet" in line):
        subsection = "sprites"
    elif ("TerminationSet" in line):
        subsection = "terminations"
    elif("LevelMapping" in line):
        subsection = "level"
    elif("InteractionSet" in line): 
        subsection = "interaction"
    
    return subsection


def parse_parts(game):
    lines = game.split("\n") 
    sprites = []
    termintions = []
    interactions = [] 
    level_mapping = []
    parent_index = 0
    subsection = ""
    begining = ""

    for line in lines: 
        line = line.split("#", 1)[0] # remove comments 
        tab_template = "   "
        line = line.replace("\t", tab_template) 
        if len(line.strip()) == 0:
            pass 
        else: 
            indent = get_indent(line)

            if subsection == "":
        
                parent_index = indent 
                subsection = get_subsection(line)
                if(subsection == ""):
                    begining += line + "\n"
            else:
                if (indent == parent_index):
                    subsection = get_subsection(line)
                else:
                    #line = line.strip()
                    #line = tab_template + tab_template + line 
                    if(subsection == "sprites"):
                        sprites.append(line)
                    elif(subsection == "terminations"):
                        termintions.append(line)
                    elif(subsection == "level"):
                        level_mapping.append(line)
                    elif(subsection == "interaction"):
                        interactions.append(line)
                
    return begining, sprites, interactions, termintions, level_mapping


def find_parent(sprites, i):
    i_ident = get_indent(sprites[i])
    j  = i -1 
    while j > 0 and get_indent(sprites[j]) >= i_ident:
        j -= 1
    
    return sprites[j]

def get_parents(sprites):
    parents = []
    parent_ident = get_indent(sprites[0])

    for i  in range(1, len(sprites)):
        print(sprites[i])
        indent = get_indent(sprites[i])
        if(indent > parent_ident):
            parent = find_parent(sprites, i)
            parents.append((parent, sprites[i]))
    return parents 



def get_games(csv_file, folder):
    games = []
    with open(csv_file) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        for row in csv_reader:
            file = open(folder + "/" + row[1])
            game = file.read()
            games.append(game)
    return games 

def get_name(sprite): 
    return sprite.split(">")[0].strip()

def get_type(rule, termination = False ):
    if(len(rule.split(">")) > 1 or termination):
        if(termination):
            words = rule.split(" ")
        else:
            words = rule.split(">")[1].split(" ")
        words = [word.strip() for word in words if len(word.strip()) > 0]
        return words[0]
    else: 
        return "None"

def interaction_sprites(interaction):
    words = interaction.split(">")[0].split(" ")
    words = [word.strip() for word in words if len(word.strip()) > 0]
    return words 

def add_param_edges(rule, rule_node, graph, sprite_name_to_node, node_to_sprite, next_node, name_map, termination = False):
    if(len(rule.split(">")) > 1 or termination):
        if(termination):
            words = rule.split(" ")
        else:
            words = rule.split(">")[1].split(" ")
        words = [word.strip() for word in words if len(word.strip()) > 0]
        for word in words: 
            if "=" in word:
                parts = word.split("=") 
                parts = [part.strip() for part in parts]
                # param is a sprite 
                if (parts[1] in name_map) and (not "img" in parts[0]): 
                    
                    """graph.add_edge(rule_node,sprite_node)
                    if(rule_node < sprite_node):
                        graph[rule_node][sprite_node][util_graph.GATTR_LABEL] = "p0_" + parts[0]
                    else: 
                        graph[rule_node][sprite_node][util_graph.GATTR_LABEL] = "p1_" + parts[0]"""
                    next_node = add_edges_to_sprite(graph, rule_node, parts[0], parts[1], sprite_name_to_node, name_map, node_to_sprite, next_node)
                else:
                    graph.add_node(next_node, label = "V_" + parts[1])
                    #graph[next_node][util_graph.GATTR_LABEL] = parts[1]
                    graph.add_edge(rule_node, next_node)
                   
                    graph[rule_node][next_node][util_graph.GATTR_LABEL] = "p_" + parts[0]
               
            
                    #print(next_node, word)
                    next_node += 1 
            
    return next_node 


def get_children_names(sprites, i):
    indent = get_indent(sprites[i])
    last_ident = indent 

    children = []
    last_children = []

    j = i + 1 
    while j < len(sprites) and get_indent(sprites[j]) > indent:

        if get_indent(sprites[j]) > last_ident:
            last_children = []
            last_ident = get_indent(sprites[j])
        elif get_indent(sprites[j]) < last_ident:
            children += last_children 
            last_children = []
            last_ident = get_indent(sprites[j])

        last_children.append(get_name(sprites[j]))

        j+= 1 
    children += last_children
    return children 

def remove_parents(sprites, name_map):
    new_sprites = []

    for sprite in sprites:
        name = get_name(sprite)
        if(len(name_map[name]) == 1):
            new_sprites.append(sprite)
    return new_sprites 
    

def get_name_map(sprites):
    m = {}

    for i in range(len(sprites)):
        name = get_name(sprites[i])
        children = get_children_names(sprites,i )
        if(len(children) == 0):
            children.append(name)
        m[name] = children 
    return m 

def combine(parent, child):
    param1 = parent.split(">")[1].strip()
    param2 = child.split(">")[1].strip()

    if(len(param1) > 0 and param1[0].isupper()):
        new_param = param1 + " " +  param2 
    else:
        new_param = param2  + " " +   param1

    return child.split(">")[0] + " > " + new_param 

def propagate_down(sprites, i):
    indent = get_indent(sprites[i])
    last_ident = indent 

    sprites = sprites[:]

    j = i + 1 
    while j < len(sprites) and get_indent(sprites[j]) > indent:

        sprites[j] = combine(sprites[i], sprites[j])

        j+= 1 
    
    
    return sprites  


def propagate_all(sprites):
    for i in range(len(sprites)):
        sprites = propagate_down(sprites, i)
    return sprites 

def add_edges_to_sprite(graph, starting_node, node_label, sprite_name, sprite_name_to_node, parent_map, node_to_sprite, next_node, use_prefix = True):
    children = parent_map[sprite_name]

    graph.add_node(next_node) 
    graph.add_edge(starting_node, next_node)
    label ="p_"  + node_label if use_prefix else  node_label 
    graph[starting_node][next_node][util_graph.GATTR_LABEL] =  label

    sprite_types = set()


    for child in children:
          child_node = sprite_name_to_node[child]
          t = get_type(node_to_sprite[child_node])
          sprite_types.add(t)
          graph.add_edge(next_node, child_node)      
          label = "s"   
          graph[next_node][child_node][util_graph.GATTR_LABEL] = label
    
    # add sprite type to label 
    if(len(sprite_types) == 1):
        sprite_type = list(sprite_types)[0]
        label = "s_" + sprite_type 
        graph.nodes[next_node][util_graph.GATTR_LABEL] = label 
    else:
        label = "s_mixed" 
        graph.nodes[next_node][util_graph.GATTR_LABEL] = label 
    
    return next_node + 1 

                


def desc_to_graph(desc):
    begining, sprites, interactions, terminations, level_mapping = parse_parts(example_game)
    graph = nx.Graph()

    sprite_to_node = {}
    sprite_name_to_node = {}
    node_to_sprite = {} 

    name_map = get_name_map(sprites)
    #print(name_map)
    sprites = propagate_all(sprites)

    sprites = remove_parents(sprites, name_map) 

    node = 0 
    for sprite in sprites:
        graph.add_node(node)
        graph.nodes[node][util_graph.GATTR_LABEL] = "S_" +  get_type(sprite)

        sprite_to_node[sprite] = node 
        sprite_name_to_node[get_name(sprite)] = node 
        node_to_sprite[node] = sprite 
        node += 1 


    for sprite, sprite_node in  sprite_to_node.items():
        node = add_param_edges(sprite, sprite_node, graph, sprite_name_to_node, node_to_sprite, node, name_map)

    for interaction in interactions: 
        interaction_node = node 
        graph.add_node(node)
        
        graph.nodes[node][util_graph.GATTR_LABEL] = "I_" + get_type(interaction)

        # add interaction edges 
        i  =0 

        for sprite in interaction_sprites(interaction):
            if(sprite in name_map):
                node = add_edges_to_sprite(graph, interaction_node, "i_" + str(i), sprite, sprite_name_to_node, name_map, node_to_sprite, node + 1, use_prefix=False)
            else: 
                
                graph.add_node(node, label = sprite)
                graph.add_edge(interaction_node, node)
                graph[interaction_node][node][util_graph.GATTR_LABEL] = "i_" + str(i)
                node += 1
            i += 1 
        

        node = add_param_edges(interaction, interaction_node, graph, sprite_name_to_node, node_to_sprite, node, name_map)

    for termination in terminations: 
        term_node = node 
        graph.add_node(node)
        graph.nodes[node][util_graph.GATTR_LABEL] = "T_" + get_type(termination, termination=True)
        node += 1 
        node = add_param_edges(termination, term_node, graph, sprite_name_to_node, node_to_sprite, node, name_map, termination=True)
        
    
    return graph

def build_params(graph, node, node_to_name, node_parents, next_group):
     params = " "
     param_dict = {}
     for i in list(graph.adj[node]):
         edge = graph.edges[node,i] 
       
         param_starter = "p_"


         if(edge[util_graph.GATTR_LABEL].startswith(param_starter)):
            param_name = edge[util_graph.GATTR_LABEL][2:]

            if(graph.nodes[i][util_graph.GATTR_LABEL].startswith("s")):
                for sprite in graph.adj[i]:
                    if graph.edges[i, sprite][util_graph.GATTR_LABEL].startswith("s"):
                        param_value = node_to_name[sprite]
                        if(param_name in param_dict):
                            param_dict[param_name].append(param_value)
                        else: 
                            param_dict[param_name] = [param_value]

            else: 
                param_value = graph.nodes[i][util_graph.GATTR_LABEL][2:]
                param_dict[param_name] = [param_value]

            
          
            #params += param_name + "=" + param_value + " "

     for name in param_dict:
        if(len(param_dict[name]) == 1):
            params += name + "=" + param_dict[name][0] + " "
        else:
            new_value, next_group = get_group_name(node_parents, param_dict[name], next_group)
            params += name + "=" + str(new_value) + " "
             

     return params, next_group 

def build_sprite(graph, node, node_to_name, node_parents, next_group): 
    t  = graph.nodes[node][util_graph.GATTR_LABEL][2:]

    sprite = node_to_name[node] + " > " + t 
    params = build_params(graph, node, node_to_name, node_parents, next_group)
    sprite += params[0]

    return sprite , params[1]

def get_interactions(graph, node_to_name, node_parents, next_group):
    interactions = []
    for node in graph.nodes.data():
        if(node[1][util_graph.GATTR_LABEL].startswith("I_")):
            interaction_type = node[1][util_graph.GATTR_LABEL][2:]
            sprite_edges = []
            for i in list(graph.adj[node[0]]):
                edge = graph.edges[node[0],i] 
                label = edge[util_graph.GATTR_LABEL] 
                if(label.startswith("i")): 

                    if(graph.nodes[i][util_graph.GATTR_LABEL].startswith("s")):
                        sprites = []
                        for sprite in graph.adj[i]:
                            if graph.edges[i, sprite][util_graph.GATTR_LABEL].startswith("s"):
                                s_name = node_to_name[sprite]
                                sprites.append(s_name)
                        if len(sprites) == 1:
                            name = sprites[0]
                        else:
                            name, next_group =  get_group_name(node_parents, sprites, next_group)
                                

                    else: 
                        name = graph.nodes[i][util_graph.GATTR_LABEL]

                    sprite_edges.append((int(label[2]),name))


            
            sprite_edges.sort(key = lambda x: x[0])
            sprite_names = ""
            for i, sprite_name in sprite_edges: 
                sprite_names += str(sprite_name) + " "
            params, next_group = build_params(graph, node[0], node_to_name, node_parents, next_group)
            inter = sprite_names + " > " + interaction_type + params
            interactions.append(inter)
    return interactions, next_group

def get_terminations(graph, node_to_name, node_parents, next_group):
    terminations = []
    for node in graph.nodes.data():
        if(node[1][util_graph.GATTR_LABEL].startswith("T_")):
            term_type = node[1][util_graph.GATTR_LABEL][2:] 
            params, next_group = build_params(graph, node[0], node_to_name, node_parents, next_group)       
            term = term_type  + params
            terminations.append(term)
    return terminations, next_group

def get_all_children(sub_dict):
    children = []
    for child in sub_dict:
        if(len(sub_dict[child].keys())) == 0:
            children.append(child)
        else:
            children += get_all_children(sub_dict[child])
    return children 


def child_in_group(name, children):
    return name in children 

def group_contains_all(children_in_dic, children_to_check):
    for child in children_to_check:
        if not child in children_in_dic:
            return False 
    return True 

"""
return true if children only 
contains names in names to check 

"""
def group_contains_only(children, names_to_check):
    if len(children) > len(names_to_check):
        return False 
    else: 
        for child in children:
            if not child_in_group(child, names_to_check):
                return False 
        return True 

def get_group_name(node_parents, name_list, next_group):
    if len(name_list) == 1:
        return name_list[0], next_group # list of one is always it's own name 
    else:
        groups_to_combine = [] 
        #print("names to check: ", name_list)
        for key in node_parents:
            sub_dict = node_parents[key]
            children_in_group = get_all_children(sub_dict)
            if(len(children_in_group) == 0): # key is already leaf node 
                children_in_group = [key]


            contains_all = group_contains_all(children_in_group, name_list)
            contains_only = group_contains_only(children_in_group, name_list)

            
            if(contains_all and contains_only): # found correct group 
                return key , next_group 
            elif(contains_only): # need to combine group 
                groups_to_combine.append(key)
            elif (contains_all): # need to make sub group 
                return get_group_name(sub_dict, name_list, next_group)
        if len(groups_to_combine) > 0: 
            new_group = {}
            for key in groups_to_combine:
                new_group[key] = node_parents[key] 
            node_parents[next_group] = new_group 

            # remove bade groups 
            for key in groups_to_combine:
                del node_parents[key]
            
            group_parts = next_group.split("_")
            new_group_name = group_parts[0] + "_" + str(int(group_parts[1]) + 1)

            return next_group, new_group_name# add 1 because we made a new group
        else:
            print("Something went wrong")
            print(node_parents)
            print(name_list)


def format_sprite(name2sprite, node_parents, starting_indent, indent_increment):
    new_sprites = []
    for key in node_parents:
        # group is a sprite 
        if key in name2sprite:
            new_sprites.append(starting_indent + name2sprite[key])
        else: # need to replace children sprites 
            new_sprites.append(starting_indent +  str(key) + " > ")
            new_sprites += format_sprite(name2sprite, node_parents[key], starting_indent + indent_increment, indent_increment)
    
    return new_sprites 



def graph_to_desc(graph):
    #print(graph.nodes)

    name_to_node = {}
    node_to_name = {}

    i = 0 
    for node in graph.nodes.data():

        if(node[1][util_graph.GATTR_LABEL].startswith("S_")):
            name = "sprite" + str(i)
            i += 1 
            name_to_node[name] = node[0]
            node_to_name[node[0]] = name 


    
    #print(graph.nodes[name_to_node["sprite0"]])
    node_parents = {}
    for name in name_to_node:
        node_parents[name] = {}
    next_group = "group_0"
    #print(build_sprite(graph, 2, node_to_name, node_parents))

    sprites = []
    name_to_sprite = {}

    for node in node_to_name:
        sprite, next_group = build_sprite(graph, node, node_to_name, node_parents, next_group)
        name_to_sprite[node_to_name[node]] = sprite 
        sprites.append(sprite)

    #print(sprites)

    interactions, next_group = get_interactions(graph, node_to_name, node_parents, next_group)
    #print(interactions)

    termintions, next_group = get_terminations(graph, node_to_name, node_parents, next_group)
    #print(termintions)

    #print(node_parents)

    tab = "     "

    sprites = format_sprite(name_to_sprite, node_parents, tab + tab, tab)

    """for sprite in sprites: 
        print(sprite)"""
    
    
    
    desc = "BasicGame\n"

    desc += tab + "SpriteSet\n"

    for sprite in sprites: 
        desc += sprite + "\n"
    
    desc += tab + "InteractionSet\n"

    for interaction in interactions: 
        desc += tab + tab +  interaction + "\n"

    desc += tab + "TerminationSet\n"

    for termaination in termintions: 
        desc += tab + tab +  termaination + "\n"

    return desc 
    



if __name__== "__main__":
    #example_game = get_games("VGDL/examples/all_games_sp.csv","VGDL" )[108]
    example_game = get_games("VGDL/examples/all_games_sp.csv","VGDL" )[0]


    
    print(example_game)
    begining, sprites, interactions, termintions, level_mapping = parse_parts(example_game)
    graph = desc_to_graph(example_game)

    desc = graph_to_desc(graph)

    print("\n\n")
    print(desc)

    for game in get_games("VGDL/examples/all_games_sp.csv","VGDL"): 
        graph = desc_to_graph(game)
        desc = graph_to_desc(graph)
    """print(graph.nodes.data())
    print("\n\n")
    print(graph.edges.data()) 
    print("\n")
    print(graph.adj[0])""" 

    """name_map = get_name_map(sprites)
    sprites = propagate_all(sprites)

    sprites = remove_parents(sprites, name_map) 
    for sprite in sprites: 
        print(sprite)"""