# Chain-of-Atom
Chain-of-Atom is the idea to teach LLM to finish a task by using a series of continuous atoms.

-----------------------------------------

### Introduction
Different from CoT, ToT, etc., CoA aims to ensure the correctness of the task result by given certain atom operations.

-----------------------------------------
### Folder Structure
```
Chain-of-Atom
├── atoms    # Atom operations
├── data_structure    # Data structure, e.g. Atom, Param, etc.
├── data    # Saved Data. e.g. Learnt atom shortcuts, etc.
├── cache    # Cache. e.g. embedding cache, etc.
├── utils    # Utils
```

-----------------------------------------
### Data Structure
* #### Atom
   Atom is the basic operation unit in CoA. It is an abstract static base class.
   Inherit it and override inputs/outputs/prompt/run... to define your own atom.
   Note that all atoms are static class, thus you must use ```@staticmethod``` or ```@classmethod``` to define methods.
* #### Thinker
   Thinker contains a language model. Instantiate it and call "think" to start a task.