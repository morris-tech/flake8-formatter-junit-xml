from flake8.formatting import base
from junit_xml import TestSuite, TestCase


class JUnitXmlFormatter(base.BaseFormatter):
    """JUnit XML formatter for Flake8."""

    # Override show_statistics to always print to stdout instead of to the file
    def show_statistics(self, statistics):
        for error_code in statistics.error_codes():
            stats_for_error_code = statistics.statistics_for(error_code)
            statistic = next(stats_for_error_code)
            count = statistic.count
            count += sum(stat.count for stat in stats_for_error_code)
            print(
                "{count:<5} {error_code} {message}".format(
                    count=count,
                    error_code=error_code,
                    message=statistic.message,
                ),
                end=self.newline
            )

    # Override show_benchmarks to always print to stdout instead of to the file.
    def show_benchmarks(self, benchmarks):
        float_format = "{value:<10.3} {statistic}".format
        int_format = "{value:<10} {statistic}".format
        for statistic, value in benchmarks:
            if isinstance(value, int):
                benchmark = int_format(statistic=statistic, value=value)
            else:
                benchmark = float_format(statistic=statistic, value=value)
            print(benchmark, end=self.newline)

    def after_init(self):
        self.test_suites = {}

    def beginning(self, filename):
        name = '{0}.{1}'.format("flake8", filename.replace('.', '_'))
        self.test_suites[filename] = TestSuite(name, file=filename)

    # This formatter overwrites the target file, in contrast to flake8 base formatter which appends to the file.
    def start(self):
        if self.filename:
            self.output_fd = open(self.filename, 'w')

    # Do not write each error
    def handle(self, error):
        name = '{0}, {1}'.format(error.code, error.text)
        test_case = TestCase(
            name,
            classname="%(path)s:%(row)d:%(col)d" % {
                "path": error.filename,
                "row": error.line_number,
                "col": error.column_number,
            },
            file=error.filename,
            line=error.line_number
        )
        test_case.add_failure_info(message=self.format(error), output=self.show_source(error))
        self.test_suites[error.filename].test_cases.append(test_case)

    def format(self, error):
        return '%(path)s:%(row)d:%(col)d: %(code)s %(text)s' % {
            "code": error.code,
            "text": error.text,
            "path": error.filename,
            "row": error.line_number,
            "col": error.column_number,
        }

    # Add a dummy test if no error found
    def finished(self, filename):
        if len(self.test_suites[filename].test_cases) == 0:
            dummy_case = TestCase("Check passed", file=filename)
            self.test_suites[filename].test_cases.append(dummy_case)

    # sort to generate a stable output
    def sorted_suites(self):
        return map(lambda x: x[1], sorted(self.test_suites.items()))

    # writes results to file after all files are processed
    def stop(self):
        self._write(TestSuite.to_xml_string(iter(self.sorted_suites())))
        super(JUnitXmlFormatter, self).stop()
