import re
import argparse


def generate_sql_query(log_file, output_file='sql_queries.sql'):
    current_lokalita = None
    with open(log_file, 'r') as file, open(output_file, 'w') as outfile:
        for line in file:
            if 'Lokalita:' in line:
                current_lokalita = re.search(
                    r'Lokalita: (.*?)$', line).group(1)
            elif 'WARNING' in line:
                match = re.search(
                    r'(ID_PLO|ID_SEG|RUIAN_IBO): \[(.*?)\]', line)
                if match:
                    identifier = match.group(1)
                    values = match.group(2)
                    outfile.write(current_lokalita + '\n')
                    sql_query = f"{identifier} IN ({values})"
                    outfile.write(sql_query + '\n\n')


def main():
    parser = argparse.ArgumentParser(
        description='Generate SQL query from log file.')
    parser.add_argument('logfile', help='The log file to process')
    parser.add_argument('-o', '--outputfile', default='sql_queries.sql',
                        help='The output file to write SQL queries')

    args = parser.parse_args()

    generate_sql_query(args.logfile, args.outputfile)


if __name__ == "__main__":
    main()
