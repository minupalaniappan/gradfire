#!/usr/bin/env ruby

require 'tempfile'
require 'optparse'

DB_NAME = 'davis_course_search'

options = {erase: false}
OptionParser.new do |opts|
    opts.banner = "Usage: updatedb.rb --erase"

    opts.on('--erase', "--erase", "Erase existing database tables") do |_|
        options[:erase] = true
    end
end.parse!

file = Tempfile.new('discourse')

system("aws s3 cp s3://gradfire/db/latest.dump #{file.path}")
if options[:erase]
    system("psql #{DB_NAME} -c 'DROP TABLE courses CASCADE;
        DROP TABLE courses_grades CASCADE;
        DROP TABLE courses_textbooks CASCADE;
        DROP TABLE instructors CASCADE;
        DROP TABLE majors CASCADE;
        DROP TABLE majors_required_courses CASCADE;
        DROP TABLE meetings CASCADE;
        DROP TABLE students_added_courses CASCADE;
        DROP TABLE students_completed_courses CASCADE;
        DROP TABLE students_course_equivalences CASCADE;
        DROP TABLE students_ge_courses CASCADE;
        DROP TABLE students_ge_progress CASCADE;
        DROP TABLE students_tentative_courses CASCADE;
        DROP TABLE textbooks_offers CASCADE;
        DROP TABLE textbooks_rentals CASCADE;'")
end
system("pg_restore -Fc -d #{DB_NAME} #{file.path}")