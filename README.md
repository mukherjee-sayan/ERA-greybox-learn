# `tLsep`: Greybox Learning of Languages Recognizable by Event-Recording Automata

This repository implements the Greybox learning algorithm `tLsep` that is proposed in the following paper, that is to appear in the proceedings of [ATVA 2024](https://atva-conference.org/2024/).

> **Greybox Learning of Languages Recognizable by Event-Recording Automata** \
> Anirban Majumdar, Sayan Mukherjee, and Jean-François Raskin

We provide a `Dockerfile` to optionally use our tool inside Docker.

## Building the Docker Image

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

## Using our Tool without a Docker Environment


### Quickstart

#### 1. Requirements

Our tool relies on the following open-source software.

  - [TChecker](https://github.com/ticktac-project/tchecker/wiki/Installation-of-TChecker) and its dependencies

  - The [Python API](https://github.com/Z3Prover/z3?tab=readme-ov-file#python) of [Z3](https://github.com/Z3Prover/z3)

#### 2. Downloading the tool

The source code of our tool can be downloded from the repository [GitHub](https://github.com/mukherjee-sayan/ERA-greybox-learn.git) using the following code.

```
git clone https://github.com/mukherjee-sayan/ERA-greybox-learn.git
```

#### 3. Instructions for running the tool on an example

The directory `tlsep` contains all the necessary files
to execute the tool, and the directory `examples` contains a few example automata that can be learnt using our tool.

To infer a new ERA (the so called, 'system under learning'), one needs to follow the syntax we use for specifying an ERA. This syntax is described in the file [file-format.md](file-format.md). 
In the input file the user needs to specify the events to be present in the automaton and mark those events whose corresponding clocks will appear on the guards, as `active`.

One also needs to specify the path to the executable `tck-reach` (which will be built when installing `TChecker`) in the file [config.py](./tlsep/config.py).

One then **needs to change the current directory** to [tlsep](./tlsep/) and then `tLsep` can be executed to learn the new automaton by executing the following:

```
cd tlsep
python3 ./tLsep.py --sul ../examples/<example-name> --m <max-constant>
```

The output of this command will be an `ERA` printed in the terminal, accepting the same language as the automaton mentioned as `sul`.

The tool has been tested in MacOS and in a Docker container running Ubuntu 22.04.