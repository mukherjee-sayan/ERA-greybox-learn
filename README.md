# `tLsep`: Greybox Learning of Languages Recognizable by Event-Recording Automata

This repository implements the Greybox learning algorithm `tLsep` that is proposed in the following paper.

> **Greybox Learning of Languages Recognizable by Event-Recording Automata** \
> Anirban Majumdar, Sayan Mukherjee, and Jean-François Raskin\
> to appear, in the proceedings of [ATVA 2024](https://atva-conference.org/2024/)

Some parts of our implementation have been inspired from the implementation of L* algorithm in [AALpy](https://github.com/DES-Lab/AALpy). We provide two methods for using our tool.

## Dependencies

Our tool relies on the following two tools:

- [TChecker](https://github.com/ticktac-project/tchecker): we use this for checking language emptiness of an ERA
- [Z3](https://github.com/Z3Prover/z3): we use the [Python API of Z3](https://github.com/Z3Prover/z3?tab=readme-ov-file#python) to check if a symbolic word is empty 

## 1. Building using Docker Image

- Install Docker as described at https://docs.docker.com/get-docker/.

- Download the source code of `tLsep` by cloning this repository.
  ```
  git clone https://github.com/mukherjee-sayan/ERA-greybox-learn.git
  ```

- From the base directory, where a `Dockerfile` resides, run the following command to build a docker image `tLsep`.

  ```
  docker build -t tLsep .
  ```
  **Note**: When building the docker image, docker clones the git repository of [TChecker](https://github.com/ticktac-project/tchecker) and installs [all its dependencies](https://github.com/ticktac-project/tchecker/wiki/Installation-of-TChecker#requirements).

- Once the image is built, it can be run using the following command:
  ```
    docker run -it tLsep 
  ```

- This will start a prompt inside the docker, where the user can use tLsep. The following command first changes the current directory to `tlsep` and then runs `tLsep.py` on one of the given example automaton.
  ```
  cd tlsep 
  python3 tLsep.py --sul ../examples/ex1.txt --m 1
  ```

## 2. Using our Tool without a Docker Environment

#### 1. Requirements

Our tool relies on the following open-source software. These must be installed before running our tool.

  - [TChecker](https://github.com/ticktac-project/tchecker/wiki/Installation-of-TChecker) and its [dependencies](https://github.com/ticktac-project/tchecker/wiki/Installation-of-TChecker#requirements)

  - The [Python API of Z3](https://github.com/Z3Prover/z3?tab=readme-ov-file#python)

#### 2. Downloading the tool

The source code of our tool can be downloded by cloning [this repository](https://github.com/mukherjee-sayan/ERA-greybox-learn.git).

```
git clone https://github.com/mukherjee-sayan/ERA-greybox-learn.git
```

#### 3. Instructions for running the tool on an example

The directory `tlsep` contains all the necessary files
to execute the tool, and the directory `examples` contains a few example automata that can be learnt using our tool.

To learn a new ERA-recognizable language, one needs to provide to the algorithm an ERA (the so-called, 'system under learning') that recognizes the target language. 
This ERA *needs to* follow the syntax described in [file-format.md](file-format.md).
In the input file, the user needs to specify the set of events of the automaton, and mark those events whose corresponding clocks will appear on the guards, as `active`. 

Before being able to run `tLsep`, the user **must** do the following: 

- the user **needs to specify the path** to the executable `tck-reach` (which will be built when installing `TChecker`) in the file [config.py](./tlsep/config.py).

- the user then **needs to change the current directory** to [tlsep](./tlsep/) 

`tLsep` can now be used to learn a new ERA by executing the following:

```
cd tlsep
python3 ./tLsep.py --sul <path-to-example-file> --m <max-constant>
```

The output of this command will be an `ERA` printed in the terminal, accepting the same language as the automaton specified as `sul`.

The tool has been tested in MacOS and in a Docker container running Ubuntu 22.04.