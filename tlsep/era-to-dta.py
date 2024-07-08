''' this file implements a function that translates
    an ERA written in the format for this tool (tLsep)
    to a DTA written in the format for the DTA-learning
    tool LearnTA '''

import argparse
import copy
# import sys

# sys.path.append('.')
# sys.path.append('./tlsep')

# import tlsep.era as era
# import tlsep.parse as parse
# import tlsep.expression as expression
# import tlsep.era as era
import era
import expression
import parse

def write_automaton(outfile, automatonname: str, a: era.ERA, clocks: str) -> None:
    
    # define the states
    outfile.write(f"    {automatonname}.states.resize({a.nstates});\n")
    for i in a.states.keys():
        outfile.write(f"    {automatonname}.states.at({i}) = std::make_shared<learnta::TAState>({str(a.states[i].accepting).lower()}); \n")

    clk_vars = dict()
    id = 0
    
    # create the clocks
    clks_str = f'    const std::array<learnta::ConstraintMaker, {len(a.events)}> {clocks} = ' + '{'
    for c in a.events:
        clk_vars[str(c)] = id
        clks_str += f'learnta::ConstraintMaker({id}),'
        id += 1
    clks_str = clks_str[:-1] + '};\n'
    outfile.write(clks_str + '\n')

    # transitions
    outfile.write('    // Transitions\n')

    for i in a.states.keys():
        for j in a.states.keys():
            # encode the transitions i --> j
            for t in a.transitions[i][j]:
                src = t.src.index() 
                tgt = t.tgt.index()
                
                guard = t.guard
                constraints_list = []
                if guard.type == 'True':
                    constraints_list = []
                elif type(guard) == expression.SimpleExpression:
                    constraints_list = [guard]
                elif type(guard) == expression.ConjExpression:
                    constraints_list = guard.list_of_constraints[:]
                else:
                    print(f'could not handle the guard {guard}')
                    raise NotImplementedError('unexpected constraint found in guards')
                
                e = t.event
                outfile.write(f"    {automatonname}.states.at({i})->next['{e}'].emplace_back();\n")
                outfile.write(f"    {automatonname}.states.at({i})->next['{e}'].back().target = {automatonname}.states.at({j}).get();\n")
                
                # create the guard
                constraints_vec = []
                for g in constraints_list:
                    op = ''
                    if g.cmp == 'lt':
                        op = '<'
                    elif g.cmp == 'le':
                        op = '<='
                    elif g.cmp == 'eq':
                        op = '=='
                    elif g.cmp == 'ge':
                        op = '>='
                    elif g.cmp == 'gt':
                        op = '>'
                    else:
                        raise TypeError('unexpected comparator operator found in a constraint')
                    assert op != ''

                    if op != '==':
                        constraints_vec.append(f'{clocks}.at({clk_vars[str(g.event)]}) {op} {g.value}')
                    else:
                        constraints_vec.append(f'{clocks}.at({clk_vars[str(g.event)]}) >= {g.value}')
                        constraints_vec.append(f'{clocks}.at({clk_vars[str(g.event)]}) <= {g.value}')
                
                # now write the guard if it is not True
                if len(constraints_vec) != 0:
                    guard_str = f"    {automatonname}.states.at({i})->next['{e}'].back().guard = std::vector<learnta::Constraint>" + '{'

                    guard_str += ','.join(constraints_vec) + '};\n'
                    
                    outfile.write(guard_str)

                # finally, write the resets
                outfile.write(f"    {automatonname}.states.at({i})->next['{e}'].back().resetVars.emplace_back({clocks}.at({clk_vars[str(e)]}), 0.0);\n\n")

    outfile.write(f'    {automatonname}.initialStates.push_back({automatonname}.states.at(0));\n')
    outfile.write(f'    {automatonname}.maxConstraints.resize({len(a.events)});\n')
    for clk_id in clk_vars.values():
        outfile.write(f'    {automatonname}.maxConstraints[{clk_id}] = 1;\n')
    outfile.write('\n')
    
    outfile.write(f'    {automatonname}.simplifyStrong();\n')
    outfile.write(f'    {automatonname}.simplifyWithZones();\n')
    outfile.write(f'    BOOST_LOG_TRIVIAL(info) << "{automatonname}:\\n" << {automatonname};\n\n')

def dera_to_dta(f: str, outfilename: str) -> str:
    ''' Arguments:
            f -- name of the file containing the description of an ERA

        Returns:
            a new file with the description written in the format of LearnTA
    '''
    with open(f, 'r') as infile:
        a = parse.build_era_from_file(f)
    
    with open(outfilename+'.cc', 'w') as outfile:
        # write the includes
        outfile.write('#include <iostream>\n')
        outfile.write('#include <memory>\n')
        outfile.write('#include <chrono>\n\n')
        
        outfile.write('#include "timed_automaton.hh"\n')
        outfile.write('#include "learner.hh"\n')
        outfile.write('#include "timed_automata_equivalence_oracle.hh"\n')
        outfile.write('#include "timed_automaton_runner.hh"\n')
        outfile.write('#include "equivalance_oracle_chain.hh"\n')
        outfile.write('#include "equivalence_oracle_by_test.hh"\n')
        outfile.write('#include "equivalence_oracle_by_random_test.hh"\n')
        outfile.write('#include "experiment_runner.hh"\n')
        outfile.write('#include "equivalence_oracle_memo.hh"\n\n')

        outfile.write('void run() {\n')
        outfile.write('    learnta::TimedAutomaton targetAutomaton, complementTargetAutomaton;\n')
        
        # write the events
        alphabet_str = ""
        for e in a.events:
            alphabet_str += "'" + str(e) + "'" + ', '
        alphabet_str = alphabet_str[:-2] # remove the ',' from the end
        outfile.write("    const std::vector<learnta::Alphabet> alphabet = {" + alphabet_str + '};\n')

        # define the states
        outfile.write('    // Generate the target DTA\n')
        write_automaton(outfile, 'targetAutomaton', a, clocks='x')

        # define the complementAutomaton
        outfile.write('    // Generate the complement of the target DTA\n')
        a_complement = copy.deepcopy(a)
        a_complement.complement()
        write_automaton(outfile, 'complementTargetAutomaton', a_complement, clocks='y')

        outfile.write('    // execute the learning\n')
        outfile.write('    learnta::ExperimentRunner runner {alphabet, targetAutomaton};\n')
        outfile.write('    runner.run();\n')
        outfile.write('}\n\n')

        outfile.write('int main(int argc, const char *argv[]) {\n')
        outfile.write('#ifdef NDEBUG\n')
        outfile.write('    boost::log::core::get()->set_filter(boost::log::trivial::severity >= boost::log::trivial::info);\n')
        outfile.write('#endif\n\n')
        outfile.write('    run();\n')
        outfile.write('    return 0;\n')
        outfile.write('}\n')

if __name__ == "__main__":
    argparser = argparse.ArgumentParser(description="convert input of tLsep to that of LearnTA")
    argparser.add_argument('--sul', dest='sul', type=str,
                                    help="filename describing the sul", 
                                    required=True, metavar="<str>")
    
    argparser.add_argument('--o', dest='outfile', type=str,
                                    help="name of the output file (without extension)", 
                                    required=True, metavar="<str>")
    
    args = argparser.parse_args()
    filename = args.sul
    outfilename = args.outfile

    dera_to_dta(filename, outfilename)
