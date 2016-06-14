from pddl.parser import Parser
import logging
def parse(domain_file, problem_file):
    # Parsing
    parser = Parser(domain_file, problem_file)
    logging.info('Parsing Domain {0}'.format(domain_file))
    domain = parser.parse_domain()
    logging.info('Parsing Problem {0}'.format(problem_file))
    problem = parser.parse_problem(domain)
    logging.debug(domain)
    logging.info('{0} Predicates parsed'.format(len(domain.predicates)))
    logging.info('{0} Actions parsed'.format(len(domain.actions)))
    logging.info('{0} Objects parsed'.format(len(problem.objects)))
    logging.info('{0} Constants parsed'.format(len(domain.constants)))
    return problem
	
problem = parse('D:\python-workspace\story-elements\domain.pddl','D:\python-workspace\story-elements\task02.pddl')
""" Problem attributes"""
        # self.name = name
        # self.domain = domain
        # self.objects = objects
        # self.initial_state = init
        # self.goal = goal
		
