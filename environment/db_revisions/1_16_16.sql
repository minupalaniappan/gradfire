update courses set title= replace(title, E'\n', ' '), description=replace(description, E'\n', ' ');
